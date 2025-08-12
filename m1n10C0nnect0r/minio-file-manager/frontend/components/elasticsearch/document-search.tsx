'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Search, Filter, Download, Eye, Copy, ChevronDown, ChevronUp } from 'lucide-react';
import { esApi } from '@/lib/es-api';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface SearchResult {
  _index: string;
  _id: string;
  _score: number;
  _source: any;
  highlight?: any;
}

interface SearchOptions {
  index: string;
  size: number;
  from: number;
  fuzzy: boolean;
  fields: string[];
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export default function DocumentSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalHits, setTotalHits] = useState(0);
  const [loading, setLoading] = useState(false);
  const [indices, setIndices] = useState<string[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);
  const [showDocDialog, setShowDocDialog] = useState(false);
  const [expandedDocs, setExpandedDocs] = useState<Set<string>>(new Set());
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const [searchOptions, setSearchOptions] = useState<SearchOptions>({
    index: '*',
    size: 20,
    from: 0,
    fuzzy: true,
    fields: ['*'],
    sortBy: '_score',
    sortOrder: 'desc'
  });

  useEffect(() => {
    fetchIndices();
  }, []);

  const fetchIndices = async () => {
    try {
      const data = await esApi.getIndices();
      setIndices(data.map(idx => idx.index));
    } catch (error) {
      console.error('Failed to fetch indices:', error);
    }
  };

  const handleSearch = async () => {
    if (!query.trim() && searchOptions.index === '*') return;
    
    setLoading(true);
    try {
      const response = await esApi.searchDocuments({
        index: searchOptions.index,
        query: query.trim() || '*',
        size: searchOptions.size,
        from: searchOptions.from,
        fuzzy: searchOptions.fuzzy,
        fields: searchOptions.fields.join(','),
        sortBy: searchOptions.sortBy,
        sortOrder: searchOptions.sortOrder
      });
      
      setResults(response.hits);
      setTotalHits(response.total);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
      setTotalHits(0);
    } finally {
      setLoading(false);
    }
  };

  const toggleDocExpand = (docId: string) => {
    const newExpanded = new Set(expandedDocs);
    if (newExpanded.has(docId)) {
      newExpanded.delete(docId);
    } else {
      newExpanded.add(docId);
    }
    setExpandedDocs(newExpanded);
  };

  const viewDocument = (doc: any) => {
    setSelectedDoc(doc);
    setShowDocDialog(true);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportResults = () => {
    const data = JSON.stringify(results, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `search_results_${Date.now()}.json`;
    a.click();
  };

  const renderHighlight = (highlight: any) => {
    if (!highlight) return null;
    
    return (
      <div className="mt-2 p-2 bg-yellow-50 rounded text-sm">
        {Object.entries(highlight).map(([field, values]) => (
          <div key={field} className="mb-1">
            <span className="font-medium text-gray-600">{field}:</span>
            <span 
              className="ml-2" 
              dangerouslySetInnerHTML={{ __html: (values as string[]).join(' ... ') }}
            />
          </div>
        ))}
      </div>
    );
  };

  const renderJsonValue = (value: any, depth = 0): JSX.Element => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400">null</span>;
    }
    
    if (typeof value === 'boolean') {
      return <span className="text-blue-600">{value.toString()}</span>;
    }
    
    if (typeof value === 'number') {
      return <span className="text-green-600">{value}</span>;
    }
    
    if (typeof value === 'string') {
      return <span className="text-orange-600">"{value}"</span>;
    }
    
    if (Array.isArray(value)) {
      if (value.length === 0) return <span>[]</span>;
      return (
        <span>[{value.map((v, i) => (
          <span key={i}>
            {renderJsonValue(v, depth + 1)}
            {i < value.length - 1 && ', '}
          </span>
        ))}]</span>
      );
    }
    
    if (typeof value === 'object') {
      const entries = Object.entries(value);
      if (entries.length === 0) return <span>{'{}'}</span>;
      
      return (
        <div className={`${depth > 0 ? 'ml-4' : ''}`}>
          {entries.map(([k, v], i) => (
            <div key={k} className="py-1">
              <span className="text-purple-600">"{k}"</span>: {renderJsonValue(v, depth + 1)}
            </div>
          ))}
        </div>
      );
    }
    
    return <span>{JSON.stringify(value)}</span>;
  };

  return (
    <div className="space-y-6">
      {/* 搜索栏 */}
      <Card>
        <CardHeader>
          <CardTitle>文档搜索</CardTitle>
          <CardDescription>在 Elasticsearch 索引中搜索文档</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex space-x-2">
              <Select
                value={searchOptions.index}
                onValueChange={(value) => setSearchOptions({...searchOptions, index: value})}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="选择索引" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="*">所有索引</SelectItem>
                  {indices.map(index => (
                    <SelectItem key={index} value={index}>{index}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Input
                placeholder="输入搜索关键词..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1"
              />
              
              <Button onClick={handleSearch} disabled={loading}>
                <Search className="w-4 h-4 mr-2" />
                搜索
              </Button>
              
              <Button
                variant="outline"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <Filter className="w-4 h-4 mr-2" />
                高级选项
              </Button>
            </div>

            {/* 高级选项 */}
            {showAdvanced && (
              <Card>
                <CardContent className="pt-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>每页结果数</Label>
                      <Slider
                        value={[searchOptions.size]}
                        onValueChange={(value) => setSearchOptions({...searchOptions, size: value[0]})}
                        min={10}
                        max={100}
                        step={10}
                      />
                      <span className="text-sm text-gray-500">{searchOptions.size} 条</span>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>排序字段</Label>
                      <Select
                        value={searchOptions.sortBy}
                        onValueChange={(value) => setSearchOptions({...searchOptions, sortBy: value})}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="_score">相关度</SelectItem>
                          <SelectItem value="upload_time">上传时间</SelectItem>
                          <SelectItem value="size">文件大小</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>排序方向</Label>
                      <Select
                        value={searchOptions.sortOrder}
                        onValueChange={(value: 'asc' | 'desc') => setSearchOptions({...searchOptions, sortOrder: value})}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="desc">降序</SelectItem>
                          <SelectItem value="asc">升序</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="fuzzy"
                        checked={searchOptions.fuzzy}
                        onCheckedChange={(checked) => setSearchOptions({...searchOptions, fuzzy: checked as boolean})}
                      />
                      <Label htmlFor="fuzzy">模糊搜索</Label>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 搜索结果 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>搜索结果</CardTitle>
              <CardDescription>
                找到 {totalHits} 个文档
              </CardDescription>
            </div>
            {results.length > 0 && (
              <Button variant="outline" size="sm" onClick={exportResults}>
                <Download className="w-4 h-4 mr-2" />
                导出结果
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-500">搜索中...</div>
          ) : results.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {query ? '未找到匹配的文档' : '请输入搜索关键词'}
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((result) => (
                <div key={result._id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <Badge variant="outline">{result._index}</Badge>
                        <Badge variant="secondary">Score: {result._score?.toFixed(2)}</Badge>
                        <span className="text-sm text-gray-500">ID: {result._id}</span>
                      </div>
                      
                      {/* 高亮显示 */}
                      {result.highlight && renderHighlight(result.highlight)}
                    </div>
                    
                    <div className="flex space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleDocExpand(result._id)}
                      >
                        {expandedDocs.has(result._id) ? 
                          <ChevronUp className="w-4 h-4" /> : 
                          <ChevronDown className="w-4 h-4" />
                        }
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => viewDocument(result)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(JSON.stringify(result._source, null, 2))}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* 文档预览 */}
                  {expandedDocs.has(result._id) && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg overflow-auto">
                      <pre className="text-sm">
                        {renderJsonValue(result._source)}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
              
              {/* 分页 */}
              {totalHits > searchOptions.size && (
                <div className="flex justify-center space-x-2 mt-4">
                  <Button
                    variant="outline"
                    disabled={searchOptions.from === 0}
                    onClick={() => {
                      setSearchOptions({
                        ...searchOptions, 
                        from: Math.max(0, searchOptions.from - searchOptions.size)
                      });
                      handleSearch();
                    }}
                  >
                    上一页
                  </Button>
                  <span className="flex items-center px-4">
                    第 {Math.floor(searchOptions.from / searchOptions.size) + 1} 页
                  </span>
                  <Button
                    variant="outline"
                    disabled={searchOptions.from + searchOptions.size >= totalHits}
                    onClick={() => {
                      setSearchOptions({
                        ...searchOptions, 
                        from: searchOptions.from + searchOptions.size
                      });
                      handleSearch();
                    }}
                  >
                    下一页
                  </Button>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 文档详情对话框 */}
      <Dialog open={showDocDialog} onOpenChange={setShowDocDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>文档详情</DialogTitle>
            <DialogDescription>
              索引: {selectedDoc?._index} | ID: {selectedDoc?._id}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4">
            <pre className="p-4 bg-gray-50 rounded-lg overflow-auto text-sm">
              {selectedDoc && JSON.stringify(selectedDoc._source, null, 2)}
            </pre>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}