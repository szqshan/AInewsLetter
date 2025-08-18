const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * 爬取2025年所有博主发过的推文
 * 支持按年份过滤和逐条保存
 */

class Tweet2025Scraper {
  constructor() {
    this.cookiesPath = path.join(__dirname, 'x_cookies.json');
    this.outputDir = path.join(__dirname, '..', 'crawled_data', 'tweets_2025');
    this.structuredDir = path.join(__dirname, '..', 'crawled_data', 'structured');
    this.browser = null;
    this.page = null;
    this.targetYear = 2025;
    this.scrapedTweetIds = new Set(); // 防止重复爬取
  }

  /**
   * 加载保存的cookies
   */
  loadCookies() {
    try {
      if (!fs.existsSync(this.cookiesPath)) {
        throw new Error('Cookie文件不存在！请先运行 export_browser_cookies.js 导出cookie');
      }
      
      const cookiesData = fs.readFileSync(this.cookiesPath, 'utf8');
      const cookies = JSON.parse(cookiesData);
      
      // 修复cookie格式以符合Playwright要求
      const fixedCookies = cookies.map(cookie => {
        const fixed = {
          name: cookie.name,
          value: cookie.value,
          domain: cookie.domain,
          path: cookie.path || '/',
          expires: cookie.expirationDate ? Math.floor(cookie.expirationDate) : undefined,
          httpOnly: cookie.httpOnly || false,
          secure: cookie.secure || false,
          sameSite: this.fixSameSite(cookie.sameSite)
        };
        
        // 移除undefined值
        Object.keys(fixed).forEach(key => {
          if (fixed[key] === undefined) {
            delete fixed[key];
          }
        });
        
        return fixed;
      });
      
      console.log(`✅ 成功加载 ${fixedCookies.length} 个cookies`);
      return fixedCookies;
      
    } catch (error) {
      console.error('❌ 加载cookies失败:', error.message);
      throw error;
    }
  }

  /**
   * 修复SameSite属性
   */
  fixSameSite(sameSite) {
    if (!sameSite || sameSite === 'unspecified') {
      return 'Lax';
    }
    if (sameSite === 'no_restriction') {
      return 'None';
    }
    return sameSite;
  }

  /**
   * 初始化浏览器
   */
  async initBrowser() {
    try {
      console.log('🚀 启动浏览器...');
      
      this.browser = await chromium.launch({
        headless: false, // 显示浏览器窗口以便调试
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu'
        ]
      });
      
      const context = await this.browser.newContext({
        viewport: { width: 1280, height: 720 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      });
      
      this.page = await context.newPage();
      
      // 加载cookies
      const cookies = this.loadCookies();
      await context.addCookies(cookies);
      
      console.log('✅ 浏览器初始化完成');
      
    } catch (error) {
      console.error('❌ 浏览器初始化失败:', error.message);
      throw error;
    }
  }

  /**
   * 导航到X主页
   */
  async navigateToHome() {
    try {
      console.log('🏠 导航到X主页...');
      
      await this.page.goto('https://x.com/home', {
        waitUntil: 'networkidle',
        timeout: 30000
      });
      
      // 等待页面加载完成
      await this.page.waitForTimeout(3000);
      
      // 检查是否成功登录
      const isLoggedIn = await this.page.$('[data-testid="SideNav_AccountSwitcher_Button"]');
      if (!isLoggedIn) {
        throw new Error('未检测到登录状态，请检查cookie是否有效');
      }
      
      console.log('✅ 成功导航到主页并确认登录状态');
      
    } catch (error) {
      console.error('❌ 导航到主页失败:', error.message);
      throw error;
    }
  }

  /**
   * 点击Following标签页
   */
  async clickFollowing() {
    try {
      console.log('👥 点击Following标签页...');
      
      // 尝试多种方式找到Following链接
      const followingSelectors = [
        'a[href="/following"]',
        'a[aria-label*="Following"]',
        'nav a[href*="following"]'
      ];
      
      let followingLink = null;
      for (const selector of followingSelectors) {
        followingLink = await this.page.$(selector);
        if (followingLink) {
          console.log(`✅ 找到Following链接: ${selector}`);
          break;
        }
      }
      
      if (!followingLink) {
        // 尝试通过文本内容查找
        followingLink = await this.page.$('xpath=//a[contains(text(), "Following")]');
      }
      
      if (!followingLink) {
        throw new Error('未找到Following链接');
      }
      
      await followingLink.click();
      await this.page.waitForTimeout(3000);
      
      console.log('✅ 成功点击Following标签页');
      
    } catch (error) {
      console.error('❌ 点击Following失败:', error.message);
      throw error;
    }
  }

  /**
   * 检查推文是否为2025年
   */
  isTweet2025(timestamp) {
    if (!timestamp) return false;
    
    try {
      const tweetDate = new Date(timestamp);
      return tweetDate.getFullYear() === this.targetYear;
    } catch (error) {
      return false;
    }
  }

  /**
   * 爬取2025年的推文
   */
  async scrape2025Tweets(maxTweets = 1000) {
    try {
      console.log(`📝 开始爬取2025年Following页面推文 (最多 ${maxTweets} 条)...`);
      
      const tweets2025 = [];
      let scrollAttempts = 0;
      const maxScrollAttempts = 50; // 增加滚动次数以获取更多历史推文
      let consecutiveNon2025Count = 0;
      const maxConsecutiveNon2025 = 20; // 连续20条非2025推文后停止
      
      while (tweets2025.length < maxTweets && scrollAttempts < maxScrollAttempts) {
        // 查找推文元素
        const tweetElements = await this.page.$$('article[data-testid="tweet"]');
        
        console.log(`🔍 当前页面找到 ${tweetElements.length} 条推文`);
        
        let foundNew2025Tweet = false;
        
        for (const tweetElement of tweetElements) {
          if (tweets2025.length >= maxTweets) break;
          
          try {
            const tweetData = await this.extractTweetData(tweetElement);
            
            if (tweetData && !this.scrapedTweetIds.has(tweetData.id)) {
              this.scrapedTweetIds.add(tweetData.id);
              
              // 检查是否为2025年推文
              if (this.isTweet2025(tweetData.timestamp)) {
                tweets2025.push(tweetData);
                foundNew2025Tweet = true;
                consecutiveNon2025Count = 0;
                
                console.log(`✅ 找到2025年推文 ${tweets2025.length}/${maxTweets}: ${tweetData.text.substring(0, 50)}...`);
                
                // 逐条保存推文
                await this.saveSingleTweet(tweetData, tweets2025.length);
              } else {
                consecutiveNon2025Count++;
                const tweetYear = new Date(tweetData.timestamp).getFullYear();
                console.log(`⏭️ 跳过${tweetYear}年推文: ${tweetData.text.substring(0, 30)}...`);
              }
            }
          } catch (error) {
            console.log('⚠️ 跳过一条推文:', error.message);
          }
        }
        
        // 如果连续多条都不是2025年推文，可能已经滚动到更早的内容
        if (consecutiveNon2025Count >= maxConsecutiveNon2025) {
          console.log(`⚠️ 连续${maxConsecutiveNon2025}条非2025年推文，可能已到达2025年之前的内容`);
          break;
        }
        
        // 滚动加载更多推文
        if (tweets2025.length < maxTweets) {
          await this.page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
          });
          
          await this.page.waitForTimeout(3000); // 增加等待时间
          scrollAttempts++;
          
          console.log(`📜 滚动加载更多推文 (${scrollAttempts}/${maxScrollAttempts})`);
        }
      }
      
      console.log(`🎉 成功爬取 ${tweets2025.length} 条2025年Following推文`);
      return tweets2025;
      
    } catch (error) {
      console.error('❌ 爬取2025年推文失败:', error.message);
      throw error;
    }
  }

  /**
   * 从推文元素中提取数据
   */
  async extractTweetData(tweetElement) {
    try {
      // 提取推文文本
      const textElement = await tweetElement.$('[data-testid="tweetText"]');
      const text = textElement ? await textElement.textContent() : '';
      
      // 提取用户名
      const usernameElement = await tweetElement.$('[data-testid="User-Name"] a');
      const username = usernameElement ? await usernameElement.textContent() : '';
      
      // 提取用户handle
      const handleElements = await tweetElement.$$('[data-testid="User-Name"] span');
      let handle = '';
      for (const handleElement of handleElements) {
        const handleText = await handleElement.textContent();
        if (handleText && handleText.startsWith('@')) {
          handle = handleText;
          break;
        }
      }
      
      // 提取时间
      const timeElement = await tweetElement.$('time');
      const timestamp = timeElement ? await timeElement.getAttribute('datetime') : '';
      
      // 提取推文链接
      const linkElement = await tweetElement.$('a[href*="/status/"]');
      const tweetUrl = linkElement ? await linkElement.getAttribute('href') : '';
      
      // 提取推文ID
      const tweetId = tweetUrl ? tweetUrl.split('/status/')[1]?.split('?')[0] : '';
      
      // 提取互动数据
      const replyElement = await tweetElement.$('[data-testid="reply"]');
      const retweetElement = await tweetElement.$('[data-testid="retweet"]');
      const likeElement = await tweetElement.$('[data-testid="like"]');
      
      const replies = replyElement ? await this.extractCount(replyElement) : 0;
      const retweets = retweetElement ? await this.extractCount(retweetElement) : 0;
      const likes = likeElement ? await this.extractCount(likeElement) : 0;
      
      // 检查是否有图片
      const imageElements = await tweetElement.$$('img[src*="pbs.twimg.com"]');
      const images = [];
      for (const imgElement of imageElements) {
        const src = await imgElement.getAttribute('src');
        if (src && src.includes('pbs.twimg.com')) {
          images.push(src);
        }
      }
      
      return {
        id: tweetId,
        text: text.trim(),
        username: username.trim(),
        handle: handle.trim(),
        timestamp: timestamp,
        url: tweetUrl ? `https://x.com${tweetUrl}` : '',
        replies: replies,
        retweets: retweets,
        likes: likes,
        images: images,
        scraped_at: new Date().toISOString()
      };
      
    } catch (error) {
      console.error('❌ 提取推文数据失败:', error.message);
      throw error;
    }
  }

  /**
   * 提取互动数量
   */
  async extractCount(element) {
    try {
      const countElement = await element.$('span[data-testid*="count"]');
      if (countElement) {
        const countText = await countElement.textContent();
        return this.parseCount(countText);
      }
      return 0;
    } catch (error) {
      return 0;
    }
  }

  /**
   * 解析数量文本 (如 1.2K -> 1200)
   */
  parseCount(countText) {
    if (!countText) return 0;
    
    const text = countText.toLowerCase().trim();
    if (text === '') return 0;
    
    const multipliers = {
      'k': 1000,
      'm': 1000000,
      'b': 1000000000
    };
    
    const lastChar = text.slice(-1);
    if (multipliers[lastChar]) {
      const number = parseFloat(text.slice(0, -1));
      return Math.round(number * multipliers[lastChar]);
    }
    
    return parseInt(text) || 0;
  }

  /**
   * 逐条保存推文（结构化存储）
   */
  async saveSingleTweet(tweetData, index) {
    try {
      // 创建结构化存储目录
      const tweetDir = path.join(this.structuredDir, `tweet_${index}_${tweetData.id}`);
      if (!fs.existsSync(tweetDir)) {
        fs.mkdirSync(tweetDir, { recursive: true });
      }
      
      // 保存metadata.json
      const metadata = {
        id: tweetData.id,
        platform: 'X',
        type: 'tweet',
        author: {
          username: tweetData.username,
          handle: tweetData.handle
        },
        content: {
          text: tweetData.text,
          images: tweetData.images
        },
        timestamps: {
          published: tweetData.timestamp,
          scraped: tweetData.scraped_at
        },
        engagement: {
          replies: tweetData.replies,
          retweets: tweetData.retweets,
          likes: tweetData.likes
        },
        urls: {
          original: tweetData.url
        }
      };
      
      const metadataPath = path.join(tweetDir, 'metadata.json');
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2), 'utf8');
      
      // 保存content.md
      const contentMd = `# ${tweetData.username} (${tweetData.handle})

${tweetData.text}

---

**发布时间:** ${new Date(tweetData.timestamp).toLocaleString('zh-CN')}
**推文链接:** ${tweetData.url}
**互动数据:** ${tweetData.replies} 回复 | ${tweetData.retweets} 转推 | ${tweetData.likes} 点赞

${tweetData.images.length > 0 ? `**图片:** ${tweetData.images.length} 张\n${tweetData.images.map(img => `- ${img}`).join('\n')}` : ''}`;
      
      const contentPath = path.join(tweetDir, 'content.md');
      fs.writeFileSync(contentPath, contentMd, 'utf8');
      
      console.log(`💾 推文 ${index} 已保存到: ${tweetDir}`);
      
    } catch (error) {
      console.error('❌ 保存单条推文失败:', error.message);
    }
  }

  /**
   * 保存所有2025年推文汇总
   */
  async saveAllTweets(tweets) {
    try {
      if (!fs.existsSync(this.outputDir)) {
        fs.mkdirSync(this.outputDir, { recursive: true });
      }
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `tweets_2025_${timestamp}.json`;
      const filepath = path.join(this.outputDir, filename);
      
      fs.writeFileSync(filepath, JSON.stringify(tweets, null, 2), 'utf8');
      
      console.log(`💾 2025年推文汇总已保存到: ${filepath}`);
      console.log(`📊 总共保存了 ${tweets.length} 条2025年推文`);
      
      // 生成统计报告
      await this.generateReport(tweets);
      
    } catch (error) {
      console.error('❌ 保存推文汇总失败:', error.message);
      throw error;
    }
  }

  /**
   * 生成爬取报告
   */
  async generateReport(tweets) {
    try {
      const report = {
        summary: {
          total_tweets: tweets.length,
          target_year: this.targetYear,
          scraped_at: new Date().toISOString(),
          date_range: {
            earliest: tweets.length > 0 ? Math.min(...tweets.map(t => new Date(t.timestamp).getTime())) : null,
            latest: tweets.length > 0 ? Math.max(...tweets.map(t => new Date(t.timestamp).getTime())) : null
          }
        },
        authors: {},
        engagement_stats: {
          total_likes: tweets.reduce((sum, t) => sum + t.likes, 0),
          total_retweets: tweets.reduce((sum, t) => sum + t.retweets, 0),
          total_replies: tweets.reduce((sum, t) => sum + t.replies, 0)
        }
      };
      
      // 统计各作者推文数量
      tweets.forEach(tweet => {
        const author = tweet.handle;
        if (!report.authors[author]) {
          report.authors[author] = {
            username: tweet.username,
            tweet_count: 0,
            total_engagement: 0
          };
        }
        report.authors[author].tweet_count++;
        report.authors[author].total_engagement += tweet.likes + tweet.retweets + tweet.replies;
      });
      
      const reportPath = path.join(this.outputDir, `report_2025_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
      fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf8');
      
      console.log(`📊 爬取报告已生成: ${reportPath}`);
      
    } catch (error) {
      console.error('❌ 生成报告失败:', error.message);
    }
  }

  /**
   * 关闭浏览器
   */
  async close() {
    try {
      if (this.browser) {
        await this.browser.close();
        console.log('✅ 浏览器已关闭');
      }
    } catch (error) {
      console.error('❌ 关闭浏览器失败:', error.message);
    }
  }

  /**
   * 主要执行函数
   */
  async run(maxTweets = 1000) {
    try {
      console.log('🚀 开始爬取2025年Following页面推文...');
      
      await this.initBrowser();
      await this.navigateToHome();
      await this.clickFollowing();
      
      const tweets2025 = await this.scrape2025Tweets(maxTweets);
      await this.saveAllTweets(tweets2025);
      
      console.log('🎉 2025年推文爬取完成！');
      
    } catch (error) {
      console.error('❌ 爬取过程中发生错误:', error.message);
      throw error;
    } finally {
      await this.close();
    }
  }
}

// 主程序入口
async function main() {
  const maxTweets = process.argv[2] ? parseInt(process.argv[2]) : 1000;
  
  console.log('============================================================');
  console.log('🕷️  X 2025年推文爬虫');
  console.log('============================================================');
  console.log(`📊 最大爬取数量: ${maxTweets}`);
  console.log(`🎯 目标年份: 2025`);
  console.log(`💾 存储方式: 逐条结构化保存`);
  console.log('============================================================');
  
  const scraper = new Tweet2025Scraper();
  
  try {
    await scraper.run(maxTweets);
  } catch (error) {
    console.error('💥 爬虫执行失败:', error.message);
    process.exit(1);
  }
}

// 处理程序中断
process.on('SIGINT', async () => {
  console.log('\n⚠️ 用户中断爬虫');
  process.exit(0);
});

if (require.main === module) {
  main();
}

module.exports = Tweet2025Scraper;