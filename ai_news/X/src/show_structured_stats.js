const fs = require('fs');
const path = require('path');

/**
 * 结构化存储统计展示器
 * 显示转换后的推文数据统计信息
 */

class StructuredStorageStats {
  constructor() {
    this.structuredDir = path.join(__dirname, '..', 'crawled_data', 'structured');
  }

  /**
   * 显示统计信息
   */
  showStats() {
    try {
      console.log('============================================================');
      console.log('📊 结构化存储统计信息');
      console.log('============================================================');
      
      if (!fs.existsSync(this.structuredDir)) {
        console.log('❌ 结构化存储目录不存在');
        return;
      }
      
      const tweetDirs = this.getTweetDirectories();
      
      if (tweetDirs.length === 0) {
        console.log('❌ 未找到任何推文数据');
        return;
      }
      
      console.log(`📁 总推文数量: ${tweetDirs.length}`);
      console.log('');
      
      let totalImages = 0;
      let totalContentSize = 0;
      const platforms = new Set();
      const authors = new Set();
      const tags = new Set();
      
      tweetDirs.forEach((tweetDir, index) => {
        const stats = this.analyzeTweetDirectory(tweetDir);
        
        console.log(`📝 推文 ${index + 1}: ${path.basename(tweetDir)}`);
        console.log(`   👤 作者: ${stats.author}`);
        console.log(`   📄 内容长度: ${stats.contentLength} 字符`);
        console.log(`   🖼️  图片数量: ${stats.imageCount}`);
        console.log(`   🏷️  标签: ${stats.tags.join(', ') || '无'}`);
        console.log(`   📅 发布时间: ${stats.publishTime}`);
        console.log('');
        
        totalImages += stats.imageCount;
        totalContentSize += stats.contentLength;
        platforms.add(stats.platform);
        authors.add(stats.author);
        stats.tags.forEach(tag => tags.add(tag));
      });
      
      console.log('============================================================');
      console.log('📈 汇总统计');
      console.log('============================================================');
      console.log(`📁 总推文数量: ${tweetDirs.length}`);
      console.log(`👥 作者数量: ${authors.size}`);
      console.log(`🖼️  总图片数量: ${totalImages}`);
      console.log(`📄 总内容长度: ${totalContentSize} 字符`);
      console.log(`🏷️  标签数量: ${tags.size}`);
      console.log(`🌐 平台: ${Array.from(platforms).join(', ')}`);
      console.log('');
      
      console.log('🏷️  热门标签:');
      Array.from(tags).forEach(tag => {
        console.log(`   - ${tag}`);
      });
      console.log('');
      
      console.log('👥 作者列表:');
      Array.from(authors).slice(0, 10).forEach(author => {
        console.log(`   - ${author}`);
      });
      
      if (authors.size > 10) {
        console.log(`   ... 还有 ${authors.size - 10} 个作者`);
      }
      
    } catch (error) {
      console.error('❌ 显示统计信息失败:', error.message);
    }
  }

  /**
   * 获取所有推文目录
   */
  getTweetDirectories() {
    try {
      return fs.readdirSync(this.structuredDir)
        .filter(item => {
          const itemPath = path.join(this.structuredDir, item);
          return fs.statSync(itemPath).isDirectory() && item.startsWith('tweet_');
        })
        .map(item => path.join(this.structuredDir, item))
        .sort();
    } catch (error) {
      console.error('❌ 获取推文目录失败:', error.message);
      return [];
    }
  }

  /**
   * 分析单个推文目录
   */
  analyzeTweetDirectory(tweetDir) {
    const stats = {
      author: '未知',
      contentLength: 0,
      imageCount: 0,
      tags: [],
      publishTime: '未知',
      platform: '未知'
    };
    
    try {
      // 读取metadata.json
      const metadataPath = path.join(tweetDir, 'metadata.json');
      if (fs.existsSync(metadataPath)) {
        const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
        stats.author = metadata.author.username;
        stats.contentLength = metadata.content.length;
        stats.imageCount = metadata.media.count;
        stats.tags = metadata.tags || [];
        stats.publishTime = metadata.timestamps.published;
        stats.platform = metadata.platform;
      }
      
      // 检查media目录
      const mediaDir = path.join(tweetDir, 'media');
      if (fs.existsSync(mediaDir)) {
        const mediaFiles = fs.readdirSync(mediaDir).filter(file => 
          file.endsWith('.jpg') || file.endsWith('.png') || file.endsWith('.gif')
        );
        stats.imageCount = Math.max(stats.imageCount, mediaFiles.length);
      }
      
    } catch (error) {
      console.error(`❌ 分析推文目录失败 (${path.basename(tweetDir)}):`, error.message);
    }
    
    return stats;
  }

  /**
   * 显示目录结构
   */
  showDirectoryStructure() {
    try {
      console.log('============================================================');
      console.log('📁 目录结构展示');
      console.log('============================================================');
      
      const tweetDirs = this.getTweetDirectories().slice(0, 3); // 只显示前3个
      
      tweetDirs.forEach((tweetDir, index) => {
        console.log(`📁 ${path.basename(tweetDir)}/`);
        
        const contentPath = path.join(tweetDir, 'content.md');
        const metadataPath = path.join(tweetDir, 'metadata.json');
        const mediaDir = path.join(tweetDir, 'media');
        
        if (fs.existsSync(contentPath)) {
          console.log('   ├── content.md');
        }
        
        if (fs.existsSync(metadataPath)) {
          console.log('   ├── metadata.json');
        }
        
        if (fs.existsSync(mediaDir)) {
          console.log('   └── media/');
          const mediaFiles = fs.readdirSync(mediaDir);
          mediaFiles.forEach((file, fileIndex) => {
            const isLast = fileIndex === mediaFiles.length - 1;
            console.log(`       ${isLast ? '└──' : '├──'} ${file}`);
          });
        }
        
        if (index < tweetDirs.length - 1) {
          console.log('');
        }
      });
      
      if (this.getTweetDirectories().length > 3) {
        console.log(`\n... 还有 ${this.getTweetDirectories().length - 3} 个推文文件夹`);
      }
      
    } catch (error) {
      console.error('❌ 显示目录结构失败:', error.message);
    }
  }
}

// 主程序入口
function main() {
  const stats = new StructuredStorageStats();
  
  const command = process.argv[2];
  
  switch (command) {
    case 'structure':
    case 'tree':
      stats.showDirectoryStructure();
      break;
    case 'stats':
    case 'summary':
    default:
      stats.showStats();
      break;
  }
}

if (require.main === module) {
  main();
}

module.exports = StructuredStorageStats;