'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  Home, 
  Search, 
  Database,
  FileText,
  Settings,
  Activity
} from 'lucide-react';

const navItems = [
  {
    title: 'MinIO 文件管理',
    href: '/',
    icon: Home,
    description: '管理存储桶和文件'
  },
  {
    title: '文件搜索',
    href: '/search',
    icon: Search,
    description: '搜索文件内容'
  },
  {
    title: 'Elasticsearch',
    href: '/elasticsearch',
    icon: Database,
    description: 'ES 管理中心'
  }
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-6">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center space-x-2">
              <Database className="w-6 h-6 text-blue-600" />
              <span className="font-bold text-lg">数据管理平台</span>
            </Link>
            
            <div className="flex space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors",
                      isActive 
                        ? "bg-blue-50 text-blue-600" 
                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{item.title}</span>
                  </Link>
                );
              })}
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Activity className="w-4 h-4" />
              <span>后端: localhost:9011</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <Activity className="w-4 h-4 text-green-500" />
              <span>ES: 连接正常</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}