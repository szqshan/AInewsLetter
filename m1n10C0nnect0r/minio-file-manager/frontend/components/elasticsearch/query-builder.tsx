'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Code, Play, Copy, Download, Save, FolderOpen } from 'lucide-react';
import { esApi } from '@/lib/es-api';

interface QueryTemplate {
  name: string;
  description: string;
  query: string;
  category: string;
}

const queryTemplates: QueryTemplate[] = [
  {
    name: '匹配所有文档',
    description: '返回索引中的所有文档',
    category: '基础查询',
    query: JSON.stringify({
      query: {
        match_all: {}
      }
    }, null, 2)
  },
  {
    name: '全文搜索',
    description: '在指定字段中搜索文本',
    category: '基础查询',
    query: JSON.stringify({
      query: {
        match: {
          "content": "搜索关键词"
        }
      }
    }, null, 2)
  },
  {
    name: '多字段搜索',
    description: '在多个字段中搜索',
    category: '基础查询',
    query: JSON.stringify({
      query: {
        multi_match: {
          query: "搜索关键词",
          fields: ["title^2", "content", "description"]
        }
      }
    }, null, 2)
  },
  {
    name: '模糊搜索',
    description: '支持拼写错误的搜索',
    category: '高级查询',
    query: JSON.stringify({
      query: {
        match: {
          content: {
            query: "搜索关键词",
            fuzziness: "AUTO"
          }
        }
      }
    }, null, 2)
  },
  {
    name: '范围查询',
    description: '查询数值或日期范围',
    category: '高级查询',
    query: JSON.stringify({
      query: {
        range: {
          upload_time: {
            gte: "2024-01-01",
            lte: "2024-12-31"
          }
        }
      }
    }, null, 2)
  },
  {
    name: '布尔组合查询',
    description: '组合多个查询条件',
    category: '高级查询',
    query: JSON.stringify({
      query: {
        bool: {
          must: [
            { match: { "status": "published" } }
          ],
          should: [
            { match: { "tags": "重要" } }
          ],
          filter: [
            { range: { "date": { gte: "2024-01-01" } } }
          ]
        }
      }
    }, null, 2)
  },
  {
    name: '聚合统计',
    description: '按字段分组统计',
    category: '聚合查询',
    query: JSON.stringify({
      size: 0,
      aggs: {
        by_type: {
          terms: {
            field: "document_type",
            size: 10
          }
        }
      }
    }, null, 2)
  },
  {
    name: '日期直方图',
    description: '按时间统计文档分布',
    category: '聚合查询',
    query: JSON.stringify({
      size: 0,
      aggs: {
        documents_over_time: {
          date_histogram: {
            field: "upload_time",
            calendar_interval: "month"
          }
        }
      }
    }, null, 2)
  }
];

export default function QueryBuilder() {
  const [query, setQuery] = useState('{\n  "query": {\n    "match_all": {}\n  }\n}');
  const [index, setIndex] = useState('*');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedQueries, setSavedQueries] = useState<QueryTemplate[]>([]);
  const [queryName, setQueryName] = useState('');

  const executeQuery = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Validate JSON
      const parsedQuery = JSON.parse(query);
      
      const response = await esApi.executeQuery({
        index,
        body: parsedQuery
      });
      
      setResults(response);
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setError('JSON 格式错误: ' + err.message);
      } else {
        setError('查询执行失败: ' + (err.message || '未知错误'));
      }
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const formatQuery = () => {
    try {
      const parsed = JSON.parse(query);
      setQuery(JSON.stringify(parsed, null, 2));
      setError(null);
    } catch (err) {
      setError('无法格式化: JSON 格式错误');
    }
  };

  const copyQuery = () => {
    navigator.clipboard.writeText(query);
  };

  const downloadQuery = () => {
    const blob = new Blob([query], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `es_query_${Date.now()}.json`;
    a.click();
  };

  const saveQuery = () => {
    if (!queryName.trim()) {
      setError('请输入查询名称');
      return;
    }
    
    const newQuery: QueryTemplate = {
      name: queryName,
      description: '自定义查询',
      category: '我的查询',
      query: query
    };
    
    setSavedQueries([...savedQueries, newQuery]);
    setQueryName('');
  };

  const loadTemplate = (template: QueryTemplate) => {
    setQuery(template.query);
    setError(null);
  };

  const renderResults = () => {
    if (!results) return null;
    
    return (
      <div className="space-y-4">
        {/* 统计信息 */}
        <div className="flex space-x-4 text-sm">
          <Badge variant="outline">
            耗时: {results.took}ms
          </Badge>
          <Badge variant="outline">
            命中: {results.hits?.total?.value || 0} 文档
          </Badge>
          <Badge variant="outline">
            最大评分: {results.hits?.max_score?.toFixed(2) || 'N/A'}
          </Badge>
        </div>
        
        {/* 结果JSON */}
        <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-[400px]">
          <pre className="text-sm">
            <code>{JSON.stringify(results, null, 2)}</code>
          </pre>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-6">
        {/* 查询模板 */}
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>查询模板</CardTitle>
            <CardDescription>选择预定义的查询模板</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="基础查询">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="基础查询">基础</TabsTrigger>
                <TabsTrigger value="高级查询">高级</TabsTrigger>
                <TabsTrigger value="聚合查询">聚合</TabsTrigger>
              </TabsList>
              
              {['基础查询', '高级查询', '聚合查询'].map(category => (
                <TabsContent key={category} value={category} className="space-y-2">
                  {queryTemplates
                    .filter(t => t.category === category)
                    .map((template, idx) => (
                      <Button
                        key={idx}
                        variant="outline"
                        className="w-full justify-start"
                        onClick={() => loadTemplate(template)}
                      >
                        <div className="text-left">
                          <div className="font-medium">{template.name}</div>
                          <div className="text-xs text-gray-500">{template.description}</div>
                        </div>
                      </Button>
                    ))}
                </TabsContent>
              ))}
            </Tabs>
            
            {/* 保存的查询 */}
            {savedQueries.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">我的查询</h4>
                <div className="space-y-2">
                  {savedQueries.map((q, idx) => (
                    <Button
                      key={idx}
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => loadTemplate(q)}
                    >
                      <FolderOpen className="w-4 h-4 mr-2" />
                      {q.name}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 查询编辑器 */}
        <Card className="col-span-2">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>查询编辑器</CardTitle>
                <CardDescription>编写和执行 Elasticsearch 查询</CardDescription>
              </div>
              <Select value={index} onValueChange={setIndex}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="*">所有索引</SelectItem>
                  <SelectItem value="minio_files">minio_files</SelectItem>
                  <SelectItem value="minio_documents">minio_documents</SelectItem>
                  <SelectItem value="newsletter_articles">newsletter_articles</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* 编辑器工具栏 */}
              <div className="flex justify-between items-center">
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline" onClick={formatQuery}>
                    <Code className="w-4 h-4 mr-2" />
                    格式化
                  </Button>
                  <Button size="sm" variant="outline" onClick={copyQuery}>
                    <Copy className="w-4 h-4 mr-2" />
                    复制
                  </Button>
                  <Button size="sm" variant="outline" onClick={downloadQuery}>
                    <Download className="w-4 h-4 mr-2" />
                    下载
                  </Button>
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="查询名称"
                    value={queryName}
                    onChange={(e) => setQueryName(e.target.value)}
                    className="px-3 py-1 border rounded"
                  />
                  <Button size="sm" variant="outline" onClick={saveQuery}>
                    <Save className="w-4 h-4 mr-2" />
                    保存
                  </Button>
                </div>
              </div>
              
              {/* 查询输入框 */}
              <Textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="font-mono text-sm"
                rows={15}
                placeholder="输入 Elasticsearch 查询 JSON..."
              />
              
              {/* 错误提示 */}
              {error && (
                <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                  {error}
                </div>
              )}
              
              {/* 执行按钮 */}
              <Button 
                className="w-full" 
                onClick={executeQuery}
                disabled={loading}
              >
                <Play className="w-4 h-4 mr-2" />
                {loading ? '执行中...' : '执行查询'}
              </Button>
              
              {/* 查询结果 */}
              {results && (
                <Card>
                  <CardHeader>
                    <CardTitle>查询结果</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {renderResults()}
                  </CardContent>
                </Card>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}