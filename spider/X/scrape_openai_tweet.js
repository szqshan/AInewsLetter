const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function scrapeOpenAITweet() {
  try {
    // 读取保存的cookie
    const cookieFile = path.join(__dirname, 'x_cookies.json');
    
    if (!fs.existsSync(cookieFile)) {
      console.error('Cookie文件不存在！请先运行 login_x.js 保存cookie');
      return;
    }
    
    const cookies = JSON.parse(fs.readFileSync(cookieFile, 'utf8'));
    console.log(`读取到 ${cookies.length} 个cookie`);
    
    // 启动浏览器
    const browser = await chromium.launch({ 
      headless: false,
      slowMo: 1000 // 慢速执行，方便观察
    });
    
    const context = await browser.newContext();
    
    // 添加cookie到浏览器上下文
    await context.addCookies(cookies);
    console.log('Cookie已加载到浏览器');
    
    const page = await context.newPage();
    
    // 导航到OpenAI官方账号页面
    console.log('正在访问OpenAI官方账号页面...');
    await page.goto('https://x.com/OpenAINewsroom');
    
    // 等待页面加载
    await page.waitForTimeout(5000);
    
    console.log('页面已加载，正在查找最新推文...');
    
    // 等待推文加载
    try {
      await page.waitForSelector('[data-testid="tweet"]', { timeout: 10000 });
      
      // 获取第一条推文（最新的）
      const firstTweet = await page.locator('[data-testid="tweet"]').first();
      
      // 提取推文内容
      const tweetText = await firstTweet.locator('[data-testid="tweetText"]').textContent() || '';
      
      // 提取用户名和时间
      const userName = await firstTweet.locator('[data-testid="User-Name"]').first().textContent() || 'OpenAI Newsroom';
      const timeElement = await firstTweet.locator('time').first();
      const tweetTime = await timeElement.getAttribute('datetime') || '';
      const displayTime = await timeElement.textContent() || '';
      
      // 检查是否有图片
      const images = await firstTweet.locator('[data-testid="tweetPhoto"] img').all();
      let imageMarkdown = '';
      
      if (images.length > 0) {
        console.log(`发现 ${images.length} 张图片，正在处理...`);
        
        for (let i = 0; i < images.length; i++) {
          const img = images[i];
          const imgSrc = await img.getAttribute('src');
          const imgAlt = await img.getAttribute('alt') || `Image ${i + 1}`;
          
          if (imgSrc) {
            imageMarkdown += `\n\n![${imgAlt}](${imgSrc})`;
          }
        }
      }
      
      // 检查是否有链接
      const links = await firstTweet.locator('a[href*="http"]').all();
      let linksMarkdown = '';
      
      if (links.length > 0) {
        console.log(`发现 ${links.length} 个链接`);
        
        for (const link of links) {
          const href = await link.getAttribute('href');
          const linkText = await link.textContent();
          
          if (href && linkText && !href.includes('x.com') && !href.includes('twitter.com')) {
            linksMarkdown += `\n\n[${linkText}](${href})`;
          }
        }
      }
      
      // 生成Markdown内容
      const markdown = `# OpenAI Newsroom - 最新推文\n\n**用户:** ${userName}\n**时间:** ${displayTime} (${tweetTime})\n**链接:** https://x.com/OpenAINewsroom\n\n## 推文内容\n\n${tweetText}${imageMarkdown}${linksMarkdown}\n\n---\n\n*抓取时间: ${new Date().toLocaleString('zh-CN')}*`;
      
      // 保存到文件
      const outputFile = path.join(__dirname, 'openai_latest_tweet.md');
      fs.writeFileSync(outputFile, markdown, 'utf8');
      
      console.log('\n🎉 推文抓取成功！');
      console.log(`📄 已保存到: ${outputFile}`);
      console.log(`📝 推文内容: ${tweetText.substring(0, 100)}${tweetText.length > 100 ? '...' : ''}`);
      console.log(`🖼️  图片数量: ${images.length}`);
      console.log(`🔗 链接数量: ${links.length}`);
      
    } catch (error) {
      console.error('获取推文时出现错误:', error.message);
      console.log('可能是页面结构发生变化或网络问题');
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
    console.error('抓取推文时出现错误:', error);
  }
}

scrapeOpenAITweet();

console.log('\n=== OpenAI推文抓取脚本 ===');
console.log('正在抓取OpenAI官方账号的最新推文...');
console.log('========================\n');