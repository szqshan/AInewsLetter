const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

/**
 * 推文数据结构化存储转换器
 * 将JSON格式的推文数据转换为标准的文件夹结构
 */

class TweetStorageConverter {
  constructor() {
    this.baseDir = path.join(__dirname, '..', 'crawled_data');
    this.structuredDir = path.join(this.baseDir, 'structured');
  }

  /**
   * 主转换函数
   */
  async convertJsonToStructured(jsonFilePath) {
    try {
      console.log('🚀 开始转换推文数据到结构化存储...');
      
      // 读取JSON文件
      const jsonData = this.loadJsonFile(jsonFilePath);
      console.log(`📊 找到 ${jsonData.length} 条推文数据`);
      
      // 创建结构化存储目录
      this.createStructuredDirectory();
      
      // 转换每条推文
      for (let i = 0; i < jsonData.length; i++) {
        const tweet = jsonData[i];
        console.log(`📝 处理推文 ${i + 1}/${jsonData.length}: ${tweet.text.substring(0, 50)}...`);
        
        await this.convertSingleTweet(tweet, i + 1);
      }
      
      console.log('🎉 所有推文数据转换完成！');
      
    } catch (error) {
      console.error('❌ 转换过程中发生错误:', error.message);
      throw error;
    }
  }

  /**
   * 读取JSON文件
   */
  loadJsonFile(filePath) {
    try {
      if (!fs.existsSync(filePath)) {
        throw new Error(`文件不存在: ${filePath}`);
      }
      
      const data = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(data);
      
    } catch (error) {
      console.error('❌ 读取JSON文件失败:', error.message);
      throw error;
    }
  }

  /**
   * 创建结构化存储目录
   */
  createStructuredDirectory() {
    try {
      if (!fs.existsSync(this.structuredDir)) {
        fs.mkdirSync(this.structuredDir, { recursive: true });
        console.log(`✅ 创建结构化存储目录: ${this.structuredDir}`);
      }
    } catch (error) {
      console.error('❌ 创建目录失败:', error.message);
      throw error;
    }
  }

  /**
   * 转换单条推文
   */
  async convertSingleTweet(tweet, index) {
    try {
      // 创建推文文件夹
      const tweetId = this.sanitizeTweetId(tweet.id);
      const tweetDir = path.join(this.structuredDir, `tweet_${index}_${tweetId}`);
      
      if (!fs.existsSync(tweetDir)) {
        fs.mkdirSync(tweetDir, { recursive: true });
      }
      
      // 创建media文件夹
      const mediaDir = path.join(tweetDir, 'media');
      if (!fs.existsSync(mediaDir)) {
        fs.mkdirSync(mediaDir, { recursive: true });
      }
      
      // 生成content.md
      await this.generateContentMd(tweet, tweetDir);
      
      // 生成metadata.json
      await this.generateMetadataJson(tweet, tweetDir);
      
      // 下载媒体文件
      if (tweet.images && tweet.images.length > 0) {
        await this.downloadMediaFiles(tweet.images, mediaDir);
      }
      
    } catch (error) {
      console.error(`❌ 转换推文失败 (${tweet.id}):`, error.message);
    }
  }

  /**
   * 清理推文ID，移除特殊字符
   */
  sanitizeTweetId(tweetId) {
    return tweetId.replace(/[^a-zA-Z0-9]/g, '_');
  }

  /**
   * 生成content.md文件
   */
  async generateContentMd(tweet, tweetDir) {
    try {
      const contentPath = path.join(tweetDir, 'content.md');
      
      const content = `# ${tweet.username} (@${tweet.handle})

## 推文内容

${tweet.text}

## 基本信息

- **发布时间**: ${tweet.timestamp || '未知'}
- **推文链接**: [查看原推文](${tweet.url})
- **用户**: ${tweet.username} (@${tweet.handle})

## 互动数据

- **回复数**: ${tweet.replies || 0}
- **转发数**: ${tweet.retweets || 0}
- **点赞数**: ${tweet.likes || 0}

## 媒体文件

${this.generateMediaMarkdown(tweet.images)}

---

*爬取时间: ${tweet.scraped_at}*
`;
      
      fs.writeFileSync(contentPath, content, 'utf8');
      
    } catch (error) {
      console.error('❌ 生成content.md失败:', error.message);
      throw error;
    }
  }

  /**
   * 生成媒体文件的Markdown
   */
  generateMediaMarkdown(images) {
    if (!images || images.length === 0) {
      return '无媒体文件';
    }
    
    return images.map((img, index) => {
      const filename = `image_${index + 1}.jpg`;
      return `![图片${index + 1}](./media/${filename})`;
    }).join('\n\n');
  }

  /**
   * 生成metadata.json文件
   */
  async generateMetadataJson(tweet, tweetDir) {
    try {
      const metadataPath = path.join(tweetDir, 'metadata.json');
      
      const metadata = {
        id: tweet.id,
        platform: 'X (Twitter)',
        type: 'tweet',
        author: {
          username: tweet.username,
          handle: tweet.handle
        },
        content: {
          text: tweet.text,
          length: tweet.text.length
        },
        timestamps: {
          published: tweet.timestamp,
          scraped: tweet.scraped_at
        },
        engagement: {
          replies: tweet.replies || 0,
          retweets: tweet.retweets || 0,
          likes: tweet.likes || 0
        },
        urls: {
          original: tweet.url,
          media: tweet.images || []
        },
        media: {
          count: tweet.images ? tweet.images.length : 0,
          types: tweet.images && tweet.images.length > 0 ? ['image'] : []
        },
        tags: this.extractTags(tweet.text),
        mentions: this.extractMentions(tweet.text),
        hashtags: this.extractHashtags(tweet.text)
      };
      
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2), 'utf8');
      
    } catch (error) {
      console.error('❌ 生成metadata.json失败:', error.message);
      throw error;
    }
  }

  /**
   * 提取标签
   */
  extractTags(text) {
    const tags = [];
    
    // AI相关关键词
    const aiKeywords = ['AI', 'ML', 'Machine Learning', 'Deep Learning', 'Neural', 'GPT', 'LLM', 'Transformer', 'PyTorch', 'TensorFlow'];
    aiKeywords.forEach(keyword => {
      if (text.toLowerCase().includes(keyword.toLowerCase())) {
        tags.push(keyword);
      }
    });
    
    return [...new Set(tags)];
  }

  /**
   * 提取@提及
   */
  extractMentions(text) {
    const mentions = text.match(/@\w+/g) || [];
    return mentions.map(mention => mention.substring(1));
  }

  /**
   * 提取#话题标签
   */
  extractHashtags(text) {
    const hashtags = text.match(/#\w+/g) || [];
    return hashtags.map(hashtag => hashtag.substring(1));
  }

  /**
   * 下载媒体文件
   */
  async downloadMediaFiles(imageUrls, mediaDir) {
    try {
      for (let i = 0; i < imageUrls.length; i++) {
        const imageUrl = imageUrls[i];
        const filename = `image_${i + 1}.jpg`;
        const filepath = path.join(mediaDir, filename);
        
        console.log(`📸 下载图片 ${i + 1}/${imageUrls.length}: ${filename}`);
        
        try {
          await this.downloadFile(imageUrl, filepath);
          console.log(`✅ 图片下载成功: ${filename}`);
        } catch (downloadError) {
          console.log(`⚠️ 图片下载失败: ${filename} - ${downloadError.message}`);
          // 创建一个占位符文件
          fs.writeFileSync(filepath + '.failed', `下载失败: ${imageUrl}\n错误: ${downloadError.message}`);
        }
      }
    } catch (error) {
      console.error('❌ 下载媒体文件失败:', error.message);
    }
  }

  /**
   * 下载单个文件
   */
  downloadFile(url, filepath) {
    return new Promise((resolve, reject) => {
      const client = url.startsWith('https:') ? https : http;
      
      const request = client.get(url, (response) => {
        if (response.statusCode === 200) {
          const fileStream = fs.createWriteStream(filepath);
          response.pipe(fileStream);
          
          fileStream.on('finish', () => {
            fileStream.close();
            resolve();
          });
          
          fileStream.on('error', (error) => {
            fs.unlink(filepath, () => {}); // 删除部分下载的文件
            reject(error);
          });
        } else {
          reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
        }
      });
      
      request.on('error', (error) => {
        reject(error);
      });
      
      request.setTimeout(30000, () => {
        request.abort();
        reject(new Error('下载超时'));
      });
    });
  }

  /**
   * 列出可用的JSON文件
   */
  listAvailableJsonFiles() {
    try {
      const files = fs.readdirSync(this.baseDir)
        .filter(file => file.endsWith('.json'))
        .map(file => path.join(this.baseDir, file));
      
      return files;
    } catch (error) {
      console.error('❌ 列出JSON文件失败:', error.message);
      return [];
    }
  }
}

// 主程序入口
async function main() {
  const converter = new TweetStorageConverter();
  
  console.log('============================================================');
  console.log('📁 推文数据结构化存储转换器');
  console.log('============================================================');
  
  try {
    // 检查命令行参数
    const jsonFilePath = process.argv[2];
    
    if (!jsonFilePath) {
      console.log('📋 可用的JSON文件:');
      const availableFiles = converter.listAvailableJsonFiles();
      
      if (availableFiles.length === 0) {
        console.log('❌ 未找到任何JSON文件');
        console.log('💡 请先运行爬虫生成推文数据');
        return;
      }
      
      availableFiles.forEach((file, index) => {
        console.log(`${index + 1}. ${path.basename(file)}`);
      });
      
      console.log('\n💡 使用方法:');
      console.log('node src\\convert_to_structured_storage.js <JSON文件路径>');
      console.log('\n示例:');
      console.log(`node src\\convert_to_structured_storage.js "${availableFiles[0]}"`);
      return;
    }
    
    // 转换数据
    await converter.convertJsonToStructured(jsonFilePath);
    
    console.log('\n🎉 转换完成！');
    console.log(`📁 结构化数据保存在: ${converter.structuredDir}`);
    
  } catch (error) {
    console.error('💥 转换失败:', error.message);
    process.exit(1);
  }
}

// 处理程序中断
process.on('SIGINT', () => {
  console.log('\n⚠️ 用户中断转换');
  process.exit(0);
});

if (require.main === module) {
  main();
}

module.exports = TweetStorageConverter;