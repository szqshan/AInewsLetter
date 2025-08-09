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

async function testImageDownload() {
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
    
    // 测试几个可能有图片的账号
    const accountsToTest = [
      'https://x.com/elonmusk',
      'https://x.com/verge',
      'https://x.com/techcrunch',
      'https://x.com/OpenAI',
      'https://x.com/OpenAINewsroom'
    ];
    
    let foundImages = false;
    
    for (const accountUrl of accountsToTest) {
      console.log(`\n🔍 正在检查账号: ${accountUrl}`);
      
      try {
        await page.goto(accountUrl);
        await page.waitForTimeout(5000);
        
        // 等待推文加载
        await page.waitForSelector('[data-testid="tweet"]', { timeout: 10000 });
        
        // 获取前几条推文
        const tweets = await page.locator('[data-testid="tweet"]').all();
        const tweetsToCheck = tweets.slice(0, 10); // 检查前10条
        
        console.log(`找到 ${tweets.length} 条推文，检查前 ${tweetsToCheck.length} 条是否有图片...`);
        
        for (let i = 0; i < tweetsToCheck.length; i++) {
          const tweet = tweetsToCheck[i];
          const images = await tweet.locator('[data-testid="tweetPhoto"] img').all();
          
          if (images.length > 0) {
            console.log(`🖼️  在推文 ${i + 1} 中发现 ${images.length} 张图片！`);
            foundImages = true;
            
            // 提取推文内容（增加超时处理）
            let tweetText = '';
            let userName = 'Unknown User';
            
            try {
              tweetText = await tweet.locator('[data-testid="tweetText"]').textContent({ timeout: 5000 }) || '';
            } catch (e) {
              console.log('⚠️  获取推文文本超时，跳过文本提取');
            }
            
            try {
              userName = await tweet.locator('[data-testid="User-Name"]').first().textContent({ timeout: 5000 }) || 'Unknown User';
            } catch (e) {
              console.log('⚠️  获取用户名超时，使用默认用户名');
            }
            
            console.log(`📝 推文内容: ${tweetText.substring(0, 100)}...`);
            console.log(`👤 用户: ${userName}`);
            
            // 下载图片
            let imageMarkdown = '';
            const downloadedImages = [];
            
            for (let j = 0; j < images.length; j++) {
              const img = images[j];
              let imgSrc = await img.getAttribute('src');
              const imgAlt = await img.getAttribute('alt') || `测试图片 ${j + 1}`;
              
              if (imgSrc) {
                try {
                  // 处理图片URL，获取高质量版本
                  if (imgSrc.includes('?')) {
                    imgSrc = imgSrc.split('?')[0] + '?format=jpg&name=large';
                  }
                  
                  // 生成本地文件名
                  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                  const fileName = `test_image_${i + 1}_${j + 1}_${timestamp}.jpg`;
                  const localPath = path.join(imagesDir, fileName);
                  
                  console.log(`📥 正在下载图片 ${j + 1}: ${fileName}`);
                  
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
                  
                  console.log(`✅ 图片 ${j + 1} 下载成功！`);
                  
                } catch (error) {
                  console.error(`❌ 下载图片 ${j + 1} 失败:`, error.message);
                }
              }
            }
            
            // 生成测试markdown
            const testMarkdown = `# 图片下载测试\n\n**账号:** ${accountUrl}\n**用户:** ${userName}\n**推文内容:** ${tweetText}\n\n## 下载的图片\n${imageMarkdown}\n\n---\n\n*测试时间: ${new Date().toLocaleString('zh-CN')}*`;
            
            // 保存测试文件
            const testFile = path.join(__dirname, 'image_download_test.md');
            fs.writeFileSync(testFile, testMarkdown, 'utf8');
            
            console.log(`\n🎉 图片下载测试成功！`);
            console.log(`📄 测试结果已保存到: ${testFile}`);
            console.log(`🖼️ 成功下载 ${downloadedImages.length} 张图片`);
            
            if (downloadedImages.length > 0) {
              console.log('\n📸 下载的图片:');
              downloadedImages.forEach((img, index) => {
                console.log(`   ${index + 1}. ${img.local}`);
              });
            }
            
            // 找到图片就停止测试
            break;
          }
        }
        
        if (foundImages) {
          break; // 找到图片就停止检查其他账号
        }
        
      } catch (error) {
        console.error(`检查账号 ${accountUrl} 时出现错误:`, error.message);
        continue;
      }
    }
    
    if (!foundImages) {
      console.log('\n😢 在所有测试账号中都没有找到包含图片的推文');
      console.log('可能这些账号最近的推文都是纯文本的');
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
    console.error('测试图片下载时出现错误:', error);
  }
}

testImageDownload();

console.log('\n=== 图片下载功能测试脚本 ===');
console.log('正在测试多个账号，寻找包含图片的推文...');
console.log('=====================================\n');