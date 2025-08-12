'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Copy, Download, RefreshCw } from 'lucide-react';
import { esApi } from '@/lib/es-api';

interface FieldMapping {
  type: string;
  analyzer?: string;
  fields?: Record<string, any>;
  properties?: Record<string, FieldMapping>;
  [key: string]: any;
}

interface IndexMapping {
  mappings: {
    properties: Record<string, FieldMapping>;
  };
  settings?: any;
}

export default function IndexMappings() {
  const [indices, setIndices] = useState<string[]>([]);
  const [selectedIndex, setSelectedIndex] = useState<string>('');
  const [mapping, setMapping] = useState<IndexMapping | null>(null);
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchIndices();
  }, []);

  const fetchIndices = async () => {
    try {
      const data = await esApi.getIndices();
      const indexNames = data.map(idx => idx.index).filter(name => !name.startsWith('.'));
      setIndices(indexNames);
      if (indexNames.length > 0 && !selectedIndex) {
        setSelectedIndex(indexNames[0]);
      }
    } catch (error) {
      console.error('Failed to fetch indices:', error);
    }
  };

  useEffect(() => {
    if (selectedIndex) {
      fetchIndexDetails();
    }
  }, [selectedIndex]);

  const fetchIndexDetails = async () => {
    if (!selectedIndex) return;
    
    setLoading(true);
    try {
      const [mappingData, settingsData] = await Promise.all([
        esApi.getIndexMapping(selectedIndex),
        esApi.getIndexSettings(selectedIndex)
      ]);
      
      setMapping(mappingData);
      setSettings(settingsData);
    } catch (error) {
      console.error('Failed to fetch index details:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFieldTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'text': 'bg-blue-100 text-blue-800',
      'keyword': 'bg-green-100 text-green-800',
      'long': 'bg-purple-100 text-purple-800',
      'integer': 'bg-purple-100 text-purple-800',
      'float': 'bg-purple-100 text-purple-800',
      'double': 'bg-purple-100 text-purple-800',
      'date': 'bg-orange-100 text-orange-800',
      'boolean': 'bg-pink-100 text-pink-800',
      'object': 'bg-gray-100 text-gray-800',
      'nested': 'bg-yellow-100 text-yellow-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const renderFieldMapping = (name: string, field: FieldMapping, path: string = '') => {
    const fullPath = path ? `${path}.${name}` : name;
    
    if (field.properties) {
      // Object or Nested type with properties
      return (
        <div key={fullPath} className="mb-4">
          <div className="flex items-center space-x-2 mb-2">
            <span className="font-medium">{name}</span>
            <Badge className={getFieldTypeColor(field.type || 'object')}>
              {field.type || 'object'}
            </Badge>
          </div>
          <div className="ml-4 pl-4 border-l-2 border-gray-200">
            {Object.entries(field.properties).map(([subName, subField]) => 
              renderFieldMapping(subName, subField, fullPath)
            )}
          </div>
        </div>
      );
    }
    
    return (
      <div key={fullPath} className="flex items-center justify-between py-2 hover:bg-gray-50 px-2 rounded">
        <div className="flex items-center space-x-2">
          <code className="text-sm font-mono">{name}</code>
          <Badge className={getFieldTypeColor(field.type)}>
            {field.type}
          </Badge>
          {field.analyzer && (
            <Badge variant="outline">
              analyzer: {field.analyzer}
            </Badge>
          )}
          {field.fields && (
            <Badge variant="secondary">
              +{Object.keys(field.fields).length} fields
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigator.clipboard.writeText(fullPath)}
        >
          <Copy className="w-3 h-3" />
        </Button>
      </div>
    );
  };

  const exportMapping = () => {
    const data = JSON.stringify({ mapping, settings }, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedIndex}_mapping_${Date.now()}.json`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* 索引选择器 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>索引映射</CardTitle>
              <CardDescription>查看索引的字段映射和设置</CardDescription>
            </div>
            <div className="flex space-x-2">
              <Select value={selectedIndex} onValueChange={setSelectedIndex}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="选择索引" />
                </SelectTrigger>
                <SelectContent>
                  {indices.map(index => (
                    <SelectItem key={index} value={index}>{index}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" size="icon" onClick={fetchIndexDetails}>
                <RefreshCw className="w-4 h-4" />
              </Button>
              {mapping && (
                <Button variant="outline" onClick={exportMapping}>
                  <Download className="w-4 h-4 mr-2" />
                  导出
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* 映射和设置 */}
      {loading ? (
        <Card>
          <CardContent className="py-8">
            <div className="text-center text-gray-500">加载中...</div>
          </CardContent>
        </Card>
      ) : mapping ? (
        <Tabs defaultValue="mappings">
          <TabsList>
            <TabsTrigger value="mappings">字段映射</TabsTrigger>
            <TabsTrigger value="settings">索引设置</TabsTrigger>
            <TabsTrigger value="raw">原始JSON</TabsTrigger>
          </TabsList>
          
          <TabsContent value="mappings">
            <Card>
              <CardHeader>
                <CardTitle>字段映射</CardTitle>
                <CardDescription>
                  共 {Object.keys(mapping.mappings?.properties || {}).length} 个顶级字段
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(mapping.mappings?.properties || {}).map(([name, field]) => 
                    renderFieldMapping(name, field)
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>索引设置</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {settings && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium mb-2">基本设置</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">分片数:</span>
                              <span>{settings.number_of_shards || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">副本数:</span>
                              <span>{settings.number_of_replicas || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">刷新间隔:</span>
                              <span>{settings.refresh_interval || '1s'}</span>
                            </div>
                          </div>
                        </div>
                        
                        {settings.analysis && (
                          <div>
                            <h4 className="font-medium mb-2">分析器</h4>
                            <div className="space-y-1 text-sm">
                              {Object.keys(settings.analysis.analyzer || {}).map(analyzer => (
                                <Badge key={analyzer} variant="outline">
                                  {analyzer}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="raw">
            <Card>
              <CardHeader>
                <CardTitle>原始 JSON</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto max-h-[500px]">
                  <pre className="text-sm">
                    <code>{JSON.stringify({ mapping, settings }, null, 2)}</code>
                  </pre>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      ) : selectedIndex ? (
        <Card>
          <CardContent className="py-8">
            <div className="text-center text-gray-500">选择一个索引查看映射</div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}