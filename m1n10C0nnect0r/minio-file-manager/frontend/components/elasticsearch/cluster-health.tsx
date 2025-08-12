'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Server, 
  HardDrive, 
  Cpu, 
  RefreshCw,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react';
import { esApi } from '@/lib/es-api';

interface ClusterHealth {
  cluster_name: string;
  status: string;
  timed_out: boolean;
  number_of_nodes: number;
  number_of_data_nodes: number;
  active_primary_shards: number;
  active_shards: number;
  relocating_shards: number;
  initializing_shards: number;
  unassigned_shards: number;
  delayed_unassigned_shards: number;
  number_of_pending_tasks: number;
  number_of_in_flight_fetch: number;
  task_max_waiting_in_queue_millis: number;
  active_shards_percent_as_number: number;
}

interface NodeStats {
  name: string;
  host: string;
  heap_percent: number;
  ram_percent: number;
  cpu: number;
  load_1m: number;
  load_5m: number;
  load_15m: number;
  disk_used_percent: number;
  node_role: string;
  master: boolean;
}

export default function ClusterHealth() {
  const [health, setHealth] = useState<ClusterHealth | null>(null);
  const [nodes, setNodes] = useState<NodeStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchClusterInfo = async () => {
    try {
      setLoading(true);
      const [healthData, nodesData] = await Promise.all([
        esApi.getClusterHealth(),
        esApi.getNodeStats()
      ]);
      
      setHealth(healthData);
      setNodes(nodesData);
    } catch (error) {
      console.error('Failed to fetch cluster info:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClusterInfo();
    
    if (autoRefresh) {
      const interval = setInterval(fetchClusterInfo, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'green':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'yellow':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'red':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'green': return 'text-green-600 bg-green-50';
      case 'yellow': return 'text-yellow-600 bg-yellow-50';
      case 'red': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getProgressColor = (value: number) => {
    if (value < 50) return 'bg-green-500';
    if (value < 80) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* 集群状态概览 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <CardTitle>集群健康状态</CardTitle>
              {health && (
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${getStatusColor(health.status)}`}>
                  {getStatusIcon(health.status)}
                  <span className="font-medium capitalize">{health.status}</span>
                </div>
              )}
            </div>
            <div className="flex space-x-2">
              <Button
                variant={autoRefresh ? "default" : "outline"}
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? '停止' : '自动'} 刷新
              </Button>
              <Button variant="outline" size="icon" onClick={fetchClusterInfo}>
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <CardDescription>
            {health?.cluster_name || 'elasticsearch'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : health ? (
            <div className="grid grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-gray-600">节点数</p>
                <p className="text-2xl font-bold">{health.number_of_nodes}</p>
                <p className="text-xs text-gray-500">数据节点: {health.number_of_data_nodes}</p>
              </div>
              
              <div className="space-y-1">
                <p className="text-sm text-gray-600">活跃分片</p>
                <p className="text-2xl font-bold">{health.active_shards}</p>
                <p className="text-xs text-gray-500">主分片: {health.active_primary_shards}</p>
              </div>
              
              <div className="space-y-1">
                <p className="text-sm text-gray-600">未分配分片</p>
                <p className="text-2xl font-bold">{health.unassigned_shards}</p>
                <p className="text-xs text-gray-500">
                  重定位: {health.relocating_shards} | 初始化: {health.initializing_shards}
                </p>
              </div>
              
              <div className="space-y-1">
                <p className="text-sm text-gray-600">分片健康度</p>
                <p className="text-2xl font-bold">{health.active_shards_percent_as_number.toFixed(1)}%</p>
                <Progress 
                  value={health.active_shards_percent_as_number} 
                  className="h-2 mt-2"
                />
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">无法获取集群状态</div>
          )}
        </CardContent>
      </Card>

      {/* 节点状态 */}
      <Card>
        <CardHeader>
          <CardTitle>节点状态</CardTitle>
          <CardDescription>集群中各节点的资源使用情况</CardDescription>
        </CardHeader>
        <CardContent>
          {nodes.length > 0 ? (
            <div className="space-y-4">
              {nodes.map((node, idx) => (
                <div key={idx} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <Server className="w-4 h-4 text-gray-500" />
                        <span className="font-medium">{node.name}</span>
                        {node.master && (
                          <Badge variant="default">Master</Badge>
                        )}
                        <Badge variant="outline">{node.node_role}</Badge>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{node.host}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">堆内存</span>
                        <span>{node.heap_percent}%</span>
                      </div>
                      <Progress 
                        value={node.heap_percent} 
                        className={`h-1.5 ${getProgressColor(node.heap_percent)}`}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">RAM</span>
                        <span>{node.ram_percent}%</span>
                      </div>
                      <Progress 
                        value={node.ram_percent} 
                        className={`h-1.5 ${getProgressColor(node.ram_percent)}`}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">CPU</span>
                        <span>{node.cpu}%</span>
                      </div>
                      <Progress 
                        value={node.cpu} 
                        className={`h-1.5 ${getProgressColor(node.cpu)}`}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">磁盘</span>
                        <span>{node.disk_used_percent}%</span>
                      </div>
                      <Progress 
                        value={node.disk_used_percent} 
                        className={`h-1.5 ${getProgressColor(node.disk_used_percent)}`}
                      />
                    </div>
                  </div>
                  
                  <div className="flex space-x-4 mt-3 text-xs text-gray-500">
                    <span>负载: {node.load_1m?.toFixed(2)} / {node.load_5m?.toFixed(2)} / {node.load_15m?.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              {loading ? '加载中...' : '暂无节点数据'}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 集群统计 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">索引操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.number_of_pending_tasks || 0}
            </div>
            <p className="text-xs text-gray-500">待处理任务</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">数据传输</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.number_of_in_flight_fetch || 0}
            </div>
            <p className="text-xs text-gray-500">进行中的提取</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">队列延迟</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.task_max_waiting_in_queue_millis || 0}ms
            </div>
            <p className="text-xs text-gray-500">最大等待时间</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}