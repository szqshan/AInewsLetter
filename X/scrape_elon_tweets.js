const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// 下载图片函数
async function downloadImage(url, filepath) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https:') ? https : http;
    
    const file = fs.createWriteStream(filepath);
    
    protocol.get(url, (response) => {
      if (response.statusCode === 200) {
        response.pipe(file);
        file.on('finish', () => {
          file.close();
          resolve(filepath);
        });
      } else {
        reject(new Error(`下载失败: ${response.statusCode}`));
      }
    }).on('error', (err) => {
      reject(err);
    });
  });
}

// 确保目录存在
function ensureDirectoryExists(dirPath) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// 处理单条推文
async function processTweet(tweet, tweetIndex, imagesDir) {
  try {
    // 提取推文内容（增加超时处理）
    let tweetText = '';
    let userName = 'Elon Musk';
    let tweetTime = '';
    let displayTime = '';
    
    try {
      tweetText = await tweet.locator('[data-testid="tweetText"]').textContent({ timeout: 5000 }) || '';
    } catch (e) {
      console.log(`⚠️  推文 ${tweetIndex + 1} 获取文本超时，跳过文本提取`);
    }
    
    try {
      userName = await tweet.locator('[data-testid="User-Name"]').first().textContent({ timeout: 5000 }) || 'Elon Musk';
    } catch (e) {
      console.log(`⚠️  推文 ${tweetIndex + 1} 获取用户名超时，使用默认用户名`);
    }
    
    try {
      const timeElement = await tweet.locator('time').first();
      tweetTime = await timeElement.getAttribute('datetime') || '';
      displayTime = await timeElement.textContent() || '';
    } catch (e) {
      console.log(`⚠️  推文 ${tweetIndex + 1} 获取时间超时，跳过时间提取`);
    }
    
    // 检查是否有图片并下载
    const images = await tweet.locator('[data-testid="tweetPhoto"] img').all();
    let imageMarkdown = '';
    const downloadedImages = [];
    
    if (images.length > 0) {
      console.log(`🖼️  推文 ${tweetIndex + 1} 发现 ${images.length} 张图片，正在下载...`);
      
      for (let i = 0; i < images.length; i++) {
        const img = images[i];
        let imgSrc = await img.getAttribute('src');
        const imgAlt = await img.getAttribute('alt') || `推文${tweetIndex + 1}图片${i + 1}`;
        
        if (imgSrc) {
          try {
            // 处理图片URL，获取高质量版本
            if (imgSrc.includes('?')) {
              imgSrc = imgSrc.split('?')[0] + '?format=jpg&name=large';
            }
            
            // 生成本地文件名
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const fileName = `elon_tweet_${tweetIndex + 1}_image_${i + 1}_${timestamp}.jpg`;
            const localPath = path.join(imagesDir, fileName);
            
            console.log(`📥 正在下载推文 ${tweetIndex + 1} 图片 ${i + 1}: ${fileName}`);
            
            // 下载图片
            await downloadImage(imgSrc, localPath);
            
            // 添加到markdown
            const relativePath = `./images/${fileName}`;
            imageMarkdown += `\n\n![${imgAlt}](${relativePath})`;
            
            downloadedImages.push({
              original: imgSrc,
              local: relativePath,
              alt: imgAlt
            });
            
            console.log(`✅ 推文 ${tweetIndex + 1} 图片 ${i + 1} 下载成功！`);
            
          } catch (error) {
            console.error(`❌ 下载推文 ${tweetIndex + 1} 图片 ${i + 1} 失败:`, error.message);
            // 如果下载失败，使用原始URL
            imageMarkdown += `\n\n![${imgAlt}](${imgSrc})`;
          }
        }
      }
    }
    
    // 检查是否有链接
    const links = await tweet.locator('a[href*="http"]').all();
    let linksMarkdown = '';
    
    if (links.length > 0) {
      console.log(`🔗 推文 ${tweetIndex + 1} 发现 ${links.length} 个链接`);
      
      for (const link of links) {
        const href = await link.getAttribute('href');
        const linkText = await link.textContent();
        
        if (href && linkText && !href.includes('x.com') && !href.includes('twitter.com')) {
          linksMarkdown += `\n\n[${linkText}](${href})`;
        }
      }
    }
    
    return {
      userName,
      displayTime,
      tweetTime,
      tweetText,
      imageMarkdown,
      linksMarkdown,
      downloadedImages,
      imageCount: images.length,
      linkCount: links.length
    };
    
  } catch (error) {
    console.error(`处理推文 ${tweetIndex + 1} 时出现错误:`, error.message);
    return null;
  }
}

async function scrapeElonTweets() {
  try {
    // 读取保存的cookie
    const cookieFile = path.join(__dirname, 'x_cookies.json');
    
    if (!fs.existsSync(cookieFile)) {
      console.error('Cookie文件不存在！请先运行 login_x.js 保存cookie');
      return;
    }
    
    const cookies = JSON.parse(fs.readFileSync(cookieFile, 'utf8'));
    console.log(`读取到 ${cookies.length} 个cookie`);
    
    // 创建images文件夹
    const imagesDir = path.join(__dirname, 'images');
    ensureDirectoryExists(imagesDir);
    
    // 启动浏览器
    const browser = await chromium.launch({ 
      headless: false,
      slowMo: 1000
    });
    
    const context = await browser.newContext();
    
    // 添加cookie到浏览器上下文
    await context.addCookies(cookies);
    console.log('Cookie已加载到浏览器');
    
    const page = await context.newPage();
    
    // 导航到Elon Musk的页面
    console.log('正在访问Elon Musk的页面...');
    await page.goto('https://x.com/elonmusk');
    
    // 等待页面加载
    await page.waitForTimeout(5000);
    
    console.log('页面已加载，正在查找最新推文...');
    
    // 等待推文加载
    try {
      await page.waitForSelector('[data-testid="tweet"]', { timeout: 10000 });
      
      // 获取前5条推文
      const tweets = await page.locator('[data-testid="tweet"]').all();
      const tweetsToProcess = tweets.slice(0, 5);
      
      console.log(`找到 ${tweets.length} 条推文，将处理前 ${tweetsToProcess.length} 条\n`);
      
      const processedTweets = [];
      let totalImages = 0;
      let totalLinks = 0;
      
      // 处理每条推文
      for (let i = 0; i < tweetsToProcess.length; i++) {
        console.log(`📝 正在处理推文 ${i + 1}/${tweetsToProcess.length}...`);
        
        const result = await processTweet(tweetsToProcess[i], i, imagesDir);
        
        if (result) {
          processedTweets.push(result);
          totalImages += result.imageCount;
          totalLinks += result.linkCount;
          
          console.log(`✅ 推文 ${i + 1} 处理完成 - 图片: ${result.imageCount}, 链接: ${result.linkCount}\n`);
        }
      }
      
      // 生成Markdown内容
      let markdownContent = `# Elon Musk 最新推文\n\n*抓取时间: ${new Date().toLocaleString('zh-CN')}*\n\n---\n\n`;
      
      processedTweets.forEach((tweet, index) => {
        markdownContent += `## 推文 ${index + 1}\n\n`;
        markdownContent += `**用户:** ${tweet.userName}\n`;
        markdownContent += `**时间:** ${tweet.displayTime}\n`;
        markdownContent += `**发布时间:** ${tweet.tweetTime}\n\n`;
        markdownContent += `**内容:**\n${tweet.tweetText}\n`;
        
        if (tweet.imageMarkdown) {
          markdownContent += `\n**图片:**${tweet.imageMarkdown}\n`;
        }
        
        if (tweet.linksMarkdown) {
          markdownContent += `\n**链接:**${tweet.linksMarkdown}\n`;
        }
        
        markdownContent += `\n---\n\n`;
      });
      
      // 添加统计信息
      markdownContent += `## 统计信息\n\n`;
      markdownContent += `- **推文总数:** ${processedTweets.length}\n`;
      markdownContent += `- **图片总数:** ${totalImages} (已下载到本地)\n`;
      markdownContent += `- **链接总数:** ${totalLinks}\n\n`;
      
      if (totalImages > 0) {
        markdownContent += `### 下载的图片\n\n`;
        processedTweets.forEach((tweet, index) => {
          if (tweet.downloadedImages.length > 0) {
            markdownContent += `**推文 ${index + 1}:**\n`;
            tweet.downloadedImages.forEach((img, imgIndex) => {
              markdownContent += `- ${img.local}\n`;
            });
            markdownContent += `\n`;
          }
        });
      }
      
      // 保存到文件
      const outputFile = path.join(__dirname, 'elon_musk_tweets.md');
      fs.writeFileSync(outputFile, markdownContent, 'utf8');
      
      console.log(`🎉 Elon Musk推文抓取成功！`);
      console.log(`📄 已保存到: ${outputFile}`);
      console.log(`📝 推文总数: ${processedTweets.length}`);
      console.log(`🖼️ 图片总数: ${totalImages} (已下载到本地)`);
      console.log(`🔗 链接总数: ${totalLinks}`);
      
    } catch (error) {
      console.error('等待推文加载失败:', error.message);
    }
    
    // 保持浏览器打开
    console.log('\n浏览器将保持打开状态，按Ctrl+C退出');
    
    // 监听退出信号
    process.on('SIGINT', async () => {
      console.log('\n正在关闭浏览器...');
      await browser.close();
      process.exit(0);
    });
    
    // 保持脚本运行
    await new Promise(() => {});
    
  } catch (error) {
    console.error('抓取Elon Musk推文时出现错误:', error);
  }
}

scrapeElonTweets();

console.log('\n=== Elon Musk推文抓取脚本 (含图片下载) ===');
console.log('正在抓取Elon Musk的最新推文并下载所有图片...');
console.log('==========================================\n');