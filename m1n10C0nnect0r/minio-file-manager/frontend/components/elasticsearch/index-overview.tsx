'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Database, 
  FileText, 
  HardDrive, 
  Activity,
  RefreshCw,
  Trash2,
  Eye
} from 'lucide-react';
import { esApi } from '@/lib/es-api';
import { formatBytes, formatNumber } from '@/lib/utils';

interface IndexInfo {
  index: string;
  health: string;
  status: string;
  uuid: string;
  docsCount: number;
  docsDeleted: number;
  storeSize: string;
  priStoreSize: string;
  shards: number;
  replicas: number;
}

interface IndexStats {
  totalIndices: number;
  totalDocuments: number;
  totalSize: string;
  avgDocumentSize: string;
}

export default function IndexOverview() {
  const [indices, setIndices] = useState<IndexInfo[]>([]);
  const [stats, setStats] = useState<IndexStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState<string | null>(null);

  const fetchIndices = async () => {
    try {
      setLoading(true);
      const data = await esApi.getIndices();
      setIndices(data);
      
      // Calculate stats
      const totalDocs = data.reduce((sum, idx) => sum + idx.docsCount, 0);
      const totalSizeBytes = data.reduce((sum, idx) => {
        const sizeStr = idx.storeSize.replace(/[^0-9.]/g, '');
        const multiplier = idx.storeSize.includes('gb') ? 1024 * 1024 * 1024 :
                          idx.storeSize.includes('mb') ? 1024 * 1024 :
                          idx.storeSize.includes('kb') ? 1024 : 1;
        return sum + (parseFloat(sizeStr) * multiplier);
      }, 0);
      
      setStats({
        totalIndices: data.length,
        totalDocuments: totalDocs,
        totalSize: formatBytes(totalSizeBytes),
        avgDocumentSize: totalDocs > 0 ? formatBytes(totalSizeBytes / totalDocs) : '0 B'
      });
    } catch (error) {
      console.error('Failed to fetch indices:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIndices();
  }, []);

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'green': return 'bg-green-500';
      case 'yellow': return 'bg-yellow-500';
      case 'red': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getHealthBadge = (health: string) => {
    const colors = {
      green: 'bg-green-100 text-green-800',
      yellow: 'bg-yellow-100 text-yellow-800',
      red: 'bg-red-100 text-red-800'
    };
    return colors[health as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总索引数</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalIndices || 0}</div>
            <p className="text-xs text-muted-foreground">活跃索引</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总文档数</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(stats?.totalDocuments || 0)}
            </div>
            <p className="text-xs text-muted-foreground">所有索引文档</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总存储大小</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalSize || '0 B'}</div>
            <p className="text-xs text-muted-foreground">磁盘占用</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均文档大小</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.avgDocumentSize || '0 B'}</div>
            <p className="text-xs text-muted-foreground">每个文档</p>
          </CardContent>
        </Card>
      </div>

      {/* 索引列表 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>索引列表</CardTitle>
              <CardDescription>管理 Elasticsearch 索引</CardDescription>
            </div>
            <Button onClick={fetchIndices} size="sm" variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {loading ? (
              <div className="text-center py-8 text-gray-500">加载中...</div>
            ) : indices.length === 0 ? (
              <div className="text-center py-8 text-gray-500">暂无索引</div>
            ) : (
              <div className="space-y-2">
                {indices.map((index) => (
                  <div
                    key={index.uuid}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${getHealthColor(index.health)}`} />
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{index.index}</span>
                          <Badge className={getHealthBadge(index.health)}>
                            {index.health}
                          </Badge>
                          <Badge variant="outline">{index.status}</Badge>
                        </div>
                        <div className="text-sm text-gray-500 mt-1">
                          {formatNumber(index.docsCount)} 文档 · {index.storeSize} · 
                          {index.shards} 分片 · {index.replicas} 副本
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedIndex(index.index)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      {!index.index.startsWith('.') && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 索引健康度分布 */}
      <Card>
        <CardHeader>
          <CardTitle>健康度分布</CardTitle>
          <CardDescription>索引健康状态统计</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {['green', 'yellow', 'red'].map((health) => {
              const count = indices.filter(idx => idx.health === health).length;
              const percentage = indices.length > 0 ? (count / indices.length) * 100 : 0;
              
              return (
                <div key={health} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize">{health}</span>
                    <span>{count} 个索引</span>
                  </div>
                  <Progress value={percentage} className={`h-2`} />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}