'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import IndexOverview from '@/components/elasticsearch/index-overview';
import DocumentSearch from '@/components/elasticsearch/document-search';
import QueryBuilder from '@/components/elasticsearch/query-builder';
import IndexMappings from '@/components/elasticsearch/index-mappings';
import ClusterHealth from '@/components/elasticsearch/cluster-health';
import { Database, Search, Code, Activity, Settings } from 'lucide-react';

export default function ElasticsearchPage() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Elasticsearch 管理中心</h1>
        <p className="text-gray-600">
          管理和查询 Elasticsearch 索引，查看集群状态，执行高级搜索
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            索引概览
          </TabsTrigger>
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Search className="w-4 h-4" />
            文档搜索
          </TabsTrigger>
          <TabsTrigger value="query" className="flex items-center gap-2">
            <Code className="w-4 h-4" />
            查询构建器
          </TabsTrigger>
          <TabsTrigger value="mappings" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            索引映射
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            集群健康
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <IndexOverview />
        </TabsContent>

        <TabsContent value="search" className="space-y-4">
          <DocumentSearch />
        </TabsContent>

        <TabsContent value="query" className="space-y-4">
          <QueryBuilder />
        </TabsContent>

        <TabsContent value="mappings" className="space-y-4">
          <IndexMappings />
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <ClusterHealth />
        </TabsContent>
      </Tabs>
    </div>
  );
}