from typing import Optional, Dict, Any, List, BinaryIO
import hashlib
import re
import html2text
import markdown
from datetime import datetime
from pathlib import Path
import mimetypes
from io import BytesIO
import logging
logger = logging.getLogger(__name__)

from app.services.minio_service import MinioService
from app.services.elasticsearch_service import ElasticsearchService
from app.services.article_processing_service import article_processing_service
from app.core.config import get_settings


class DocumentPipelineService:

    CONFIGURABLE_DOCUMENT_TYPES = {
        'markdown': ['.md', '.markdown'],
        'html': ['.html', '.htm'],
        'text': ['.txt'],
        'rst': ['.rst'],
    }

    MIME_TYPE_MAP = {
        'text/markdown': 'markdown',
        'text/x-markdown': 'markdown',
        'text/html': 'html',
        'application/xhtml+xml': 'html',
        'text/plain': 'text',
        'text/x-rst': 'rst',
    }

    def __init__(self):
        self.minio_service = MinioService()
        self.es_service = ElasticsearchService()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.settings = get_settings()
        self.enabled_types = self._load_enabled_types()

    def _load_enabled_types(self) -> List[str]:
        enabled = self.settings.document_pipeline_types
        return enabled if isinstance(enabled, list) else ['markdown', 'html']

    def is_document_file(self, filename: str, content_type: Optional[str] = None) -> bool:
        file_ext = Path(filename).suffix.lower()
        logger.info(f'file_ext: {file_ext}  ')
        for doc_type, extensions in self.CONFIGURABLE_DOCUMENT_TYPES.items():
            if doc_type in self.enabled_types and file_ext in extensions:
                return True

        if content_type and content_type in self.MIME_TYPE_MAP:
            doc_type = self.MIME_TYPE_MAP[content_type]
            return doc_type in self.enabled_types

        return False

    def extract_content(self, file_content: bytes, filename: str, content_type: Optional[str] = None) -> Dict[str, Any]:
        file_ext = Path(filename).suffix.lower()
        content_str = file_content.decode('utf-8', errors='ignore')

        plain_text = ""
        html_content = ""
        metadata = {}

        if file_ext in ['.md', '.markdown'] or content_type in ['text/markdown', 'text/x-markdown']:
            html_content = markdown.markdown(content_str, extensions=['extra', 'codehilite', 'tables'])
            plain_text = self.html_converter.handle(html_content)
            metadata['format'] = 'markdown'

            title_match = re.search(r'^#\s+(.+)$', content_str, re.MULTILINE)
            if title_match:
                metadata['title'] = title_match.group(1).strip()

            metadata['headings'] = re.findall(r'^#{1,6}\s+(.+)$', content_str, re.MULTILINE)

            code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content_str, re.DOTALL)
            metadata['has_code'] = len(code_blocks) > 0
            metadata['code_blocks_count'] = len(code_blocks)

        elif file_ext in ['.html', '.htm'] or content_type in ['text/html', 'application/xhtml+xml']:
            html_content = content_str
            plain_text = self.html_converter.handle(content_str)
            metadata['format'] = 'html'

            title_match = re.search(r'<title>(.*?)</title>', content_str, re.IGNORECASE | re.DOTALL)
            if title_match:
                metadata['title'] = title_match.group(1).strip()

            meta_tags = re.findall(r'<meta\s+name=["\'](.*?)["\']\s+content=["\'](.*?)["\']', content_str, re.IGNORECASE)
            for name, content in meta_tags:
                if name.lower() in ['description', 'keywords', 'author']:
                    metadata[name.lower()] = content

        elif file_ext in ['.txt'] or content_type == 'text/plain':
            plain_text = content_str
            metadata['format'] = 'text'

            lines = content_str.split('\n')
            if lines:
                metadata['title'] = lines[0][:100].strip()

        elif file_ext in ['.rst']:
            metadata['format'] = 'rst'
            plain_text = content_str

            title_match = re.search(r'^(.+)\n[=\-]{3,}', content_str, re.MULTILINE)
            if title_match:
                metadata['title'] = title_match.group(1).strip()

        content_hash = hashlib.sha256(file_content).hexdigest()

        word_count = len(plain_text.split())
        char_count = len(plain_text)
        line_count = plain_text.count('\n') + 1

        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', plain_text)

        return {
            'content': plain_text[:50000],
            'content_full': plain_text if len(plain_text) <= 50000 else None,
            'html_content': html_content[:50000] if html_content else None,
            'content_hash': content_hash,
            'metadata': metadata,
            'statistics': {
                'word_count': word_count,
                'char_count': char_count,
                'line_count': line_count,
                'url_count': len(urls)
            },
            'extracted_urls': urls[:100]
        }

    async def process_upload(
        self,
        bucket_name: str,
        file_name: str,
        file_content: bytes,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:

        result = {
            'minio_upload': False,
            'es_indexed': False,
            'public_url': None,
            'es_document_id': None,
            'error': None
        }

        try:
            upload_result = await self.minio_service.upload_file(
                bucket_name=bucket_name,
                object_name=file_name,
                file_data=BytesIO(file_content),
                content_type=content_type or mimetypes.guess_type(file_name)[0]
            )
            result['minio_upload'] = True
            if isinstance(upload_result, dict) and 'etag' in upload_result:
                result['etag'] = upload_result['etag']

            public_url = None
            try:
                public_info = await self.minio_service.get_public_url(bucket_name, file_name)
                public_url = public_info.get('public_url') if isinstance(public_info, dict) else None
                result['public_url'] = public_url
            except:
                presigned_url = self.minio_service.client.presigned_get_object(
                    bucket_name, file_name, expires=3600*24*7
                )
                result['public_url'] = presigned_url

            if self.is_document_file(file_name, content_type):
                # 使用新的文章处理服务进行索引
                article_result = await article_processing_service.process_and_index(
                    bucket_name=bucket_name,
                    object_name=file_name,
                    file_content=file_content,
                    content_type=content_type
                )

                if article_result['success']:
                    result['es_indexed'] = True
                    result['es_document_id'] = article_result['doc_id']
                    result['pg_id'] = article_result.get('pg_id')
                    result['index_name'] = article_result['index']
                    result['is_duplicate'] = article_result.get('is_duplicate', False)
                else:
                    # 如果新服务失败，使用旧的索引方式作为备份
                    extracted_data = self.extract_content(file_content, file_name, content_type)

                    es_document = {
                        'bucket_name': bucket_name,
                        'object_name': file_name,
                        'size': len(file_content),
                        'content_type': content_type or mimetypes.guess_type(file_name)[0],
                        'upload_time': datetime.utcnow().isoformat(),
                        'minio_public_url': result['public_url'],
                        'content': extracted_data['content'],
                        'content_full': extracted_data.get('content_full'),
                        'html_content': extracted_data.get('html_content'),
                        'content_hash': extracted_data['content_hash'],
                        'document_metadata': extracted_data['metadata'],
                        'statistics': extracted_data['statistics'],
                        'extracted_urls': extracted_data['extracted_urls'],
                        'document_type': extracted_data['metadata'].get('format', 'unknown'),
                        'title': extracted_data['metadata'].get('title', file_name),
                        'searchable': True
                    }

                    if 'description' in extracted_data['metadata']:
                        es_document['description'] = extracted_data['metadata']['description']
                    if 'keywords' in extracted_data['metadata']:
                        es_document['keywords'] = extracted_data['metadata']['keywords'].split(',')
                    if 'author' in extracted_data['metadata']:
                        es_document['author'] = extracted_data['metadata']['author']

                    index_result = await self.es_service.index_document(
                        index_name='minio_documents',
                        document=es_document,
                        document_id=extracted_data['content_hash']
                    )

                    result['es_indexed'] = True
                    result['es_document_id'] = extracted_data['content_hash']

            return result

        except Exception as e:
            result['error'] = str(e)
            return result

    async def search_documents(
        self,
        query: str,
        bucket_name: Optional[str] = None,
        document_type: Optional[str] = None,
        fuzzy: bool = True,
        size: int = 20
    ) -> List[Dict[str, Any]]:

        must_conditions = []
        should_conditions = []

        if fuzzy:
            should_conditions.extend([
                {"match": {"content": {"query": query, "fuzziness": "AUTO"}}},
                {"match": {"title": {"query": query, "fuzziness": "AUTO", "boost": 2.0}}},
                {"match": {"description": {"query": query, "fuzziness": "AUTO", "boost": 1.5}}},
                {"match": {"keywords": {"query": query, "boost": 1.5}}},
                {"match_phrase_prefix": {"content": {"query": query}}},
                {"wildcard": {"title": f"*{query.lower()}*"}}
            ])
        else:
            should_conditions.extend([
                {"match": {"content": query}},
                {"match": {"title": {"query": query, "boost": 2.0}}},
                {"match": {"description": {"query": query, "boost": 1.5}}}
            ])

        if bucket_name:
            must_conditions.append({"term": {"bucket_name": bucket_name}})

        if document_type:
            must_conditions.append({"term": {"document_type": document_type}})

        search_body = {
            "query": {
                "bool": {
                    "must": must_conditions if must_conditions else [{"match_all": {}}],
                    "should": should_conditions,
                    "minimum_should_match": 1 if should_conditions else 0
                }
            },
            "size": size,
            "highlight": {
                "fields": {
                    "content": {"fragment_size": 150, "number_of_fragments": 3},
                    "title": {},
                    "description": {}
                }
            },
            "_source": {
                "excludes": ["content_full", "html_content"]
            }
        }

        results = await self.es_service.search(
            index_name='minio_documents',
            body=search_body
        )

        documents = []
        for hit in results.get('hits', {}).get('hits', []):
            doc = hit['_source']
            doc['_score'] = hit['_score']
            doc['_id'] = hit['_id']
            if 'highlight' in hit:
                doc['_highlight'] = hit['highlight']
            documents.append(doc)

        return documents

    async def get_similar_documents(
        self,
        document_id: str,
        size: int = 10
    ) -> List[Dict[str, Any]]:

        try:
            doc_result = await self.es_service.get_document(
                index_name='minio_documents',
                document_id=document_id
            )

            if not doc_result or '_source' not in doc_result:
                return []

            source = doc_result['_source']

            more_like_this_query = {
                "query": {
                    "more_like_this": {
                        "fields": ["content", "title", "description", "keywords"],
                        "like": [
                            {
                                "_index": "minio_documents",
                                "_id": document_id
                            }
                        ],
                        "min_term_freq": 1,
                        "max_query_terms": 25,
                        "min_doc_freq": 1,
                        "minimum_should_match": "30%"
                    }
                },
                "size": size,
                "_source": {
                    "excludes": ["content_full", "html_content"]
                }
            }

            results = await self.es_service.search(
                index_name='minio_documents',
                body=more_like_this_query
            )

            documents = []
            for hit in results.get('hits', {}).get('hits', []):
                if hit['_id'] != document_id:
                    doc = hit['_source']
                    doc['_score'] = hit['_score']
                    doc['_id'] = hit['_id']
                    documents.append(doc)

            return documents

        except Exception as e:
            print(f"Error getting similar documents: {e}")
            return []


document_pipeline_service = DocumentPipelineService()
