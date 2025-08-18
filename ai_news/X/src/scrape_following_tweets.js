const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * 爬取用户Following页面的推文
 * 使用已保存的cookie进行认证
 */

class FollowingTweetsScraper {
  constructor(timeFilter = null) {
    this.cookiesPath = path.join(__dirname, 'x_cookies.json');
    this.outputDir = path.join(__dirname, '..', 'crawled_data');
    this.structuredDir = path.join(__dirname, '..', 'crawled_data');
    this.browser = null;
    this.page = null;
    this.timeFilter = timeFilter; // 时间过滤器，支持多种格式
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
      
      console.log(`✅ 成功加载并修复 ${fixedCookies.length} 个cookies`);
      return fixedCookies;
    } catch (error) {
      console.error('❌ 加载cookies失败:', error.message);
      throw error;
    }
  }

  /**
   * 修复sameSite属性
   */
  fixSameSite(sameSite) {
    if (!sameSite) return 'Lax';
    
    const sameSiteMap = {
      'no_restriction': 'None',
      'lax': 'Lax',
      'strict': 'Strict',
      'none': 'None'
    };
    
    return sameSiteMap[sameSite.toLowerCase()] || 'Lax';
  }

  /**
   * 启动浏览器并设置cookies
   */
  async initBrowser() {
    try {
      console.log('🚀 启动浏览器...');
      
      this.browser = await chromium.launch({
        headless: false, // 设置为可见模式，方便调试
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-web-security',
          '--disable-features=VizDisplayCompositor',
          '--disable-blink-features=AutomationControlled',
          '--disable-extensions',
          '--no-first-run',
          '--disable-default-apps',
          '--disable-background-timer-throttling',
          '--disable-backgrounding-occluded-windows',
          '--disable-renderer-backgrounding'
        ]
      });
      
      const context = await this.browser.newContext({
        viewport: { width: 1280, height: 720 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        extraHTTPHeaders: {
          'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7'
        }
      });
      
      // 加载cookies
      const cookies = this.loadCookies();
      await context.addCookies(cookies);
      
      this.page = await context.newPage();
      
      // 隐藏webdriver特征
      await this.page.addInitScript(() => {
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined,
        });
        
        // 覆盖plugins属性
        Object.defineProperty(navigator, 'plugins', {
          get: () => [1, 2, 3, 4, 5],
        });
        
        // 覆盖languages属性
        Object.defineProperty(navigator, 'languages', {
          get: () => ['en-US', 'en', 'zh-CN', 'zh'],
        });
        
        // 覆盖chrome属性
        window.chrome = {
          runtime: {},
        };
        
        // 覆盖permissions属性
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
          parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
      });
      
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
    const maxRetries = 3;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`🏠 导航到X主页... (尝试 ${attempt}/${maxRetries})`);
        
        // 先尝试访问X首页，然后再跳转到home
        if (attempt === 1) {
          await this.page.goto('https://x.com', {
            waitUntil: 'domcontentloaded',
            timeout: 60000
          });
          
          await this.page.waitForTimeout(2000);
        }
        
        await this.page.goto('https://x.com/home', {
          waitUntil: 'domcontentloaded',
          timeout: 60000
        });
        
        // 等待页面加载完成
        await this.page.waitForTimeout(5000);
        
        // 检查是否成功登录
        const isLoggedIn = await this.page.$('[data-testid="SideNav_AccountSwitcher_Button"]') || 
                          await this.page.$('[data-testid="AppTabBar_Home_Link"]') ||
                          await this.page.$('nav[role="navigation"]');
        
        if (isLoggedIn) {
          console.log('✅ 成功到达X主页并确认登录状态');
          return;
        } else {
          console.log('⚠️ 页面加载完成但未检测到登录状态，继续尝试...');
        }
        
      } catch (error) {
        console.error(`❌ 第${attempt}次导航失败:`, error.message);
        
        if (attempt === maxRetries) {
          throw error;
        }
        
        console.log(`⏳ 等待 ${attempt * 2} 秒后重试...`);
        await this.page.waitForTimeout(attempt * 2000);
      }
    }
  }

  /**
   * 检查推文时间是否在用户需求范围内
   */
  isTweetInTimeRange(timestamp) {
    // 如果没有设置时间过滤器，包含所有推文
    if (!this.timeFilter) return true;
    
    // 如果没有时间戳，跳过该推文（可能是广告）
    if (!timestamp || timestamp.trim() === '') {
      console.log('⚠️ 推文缺少时间戳，可能是广告推文，跳过');
      return false;
    }
    
    try {
      const tweetDate = new Date(timestamp);
      
      // 检查日期是否有效
      if (isNaN(tweetDate.getTime())) {
        console.log(`⚠️ 推文时间戳无效: ${timestamp}，跳过`);
        return false;
      }
      
      // 根据时间过滤器类型进行判断
      return this.checkTimeFilter(tweetDate);
    } catch (error) {
      console.log(`⚠️ 时间解析失败: ${timestamp}，跳过`);
      return false;
    }
  }

  /**
   * 根据时间过滤器检查推文时间
   */
  checkTimeFilter(tweetDate) {
    const filter = this.timeFilter;
    
    // 如果是数字，当作年份处理（向后兼容）
    if (typeof filter === 'number') {
      const tweetYear = tweetDate.getFullYear();
      if (tweetYear < 2006 || tweetYear > 2030) {
        console.log(`⚠️ 推文年份超出合理范围: ${tweetYear}，跳过`);
        return false;
      }
      return tweetYear === filter;
    }
    
    // 如果是对象，支持更复杂的时间范围
    if (typeof filter === 'object') {
      // 支持年份范围: {startYear: 2024, endYear: 2025}
      if (filter.startYear || filter.endYear) {
        const tweetYear = tweetDate.getFullYear();
        if (filter.startYear && tweetYear < filter.startYear) return false;
        if (filter.endYear && tweetYear > filter.endYear) return false;
        return true;
      }
      
      // 支持日期范围: {startDate: '2024-01-01', endDate: '2024-12-31'}
      if (filter.startDate || filter.endDate) {
        if (filter.startDate) {
          const startDate = new Date(filter.startDate);
          if (tweetDate < startDate) return false;
        }
        if (filter.endDate) {
          const endDate = new Date(filter.endDate);
          if (tweetDate > endDate) return false;
        }
        return true;
      }
      
      // 支持相对时间: {days: 7} 表示最近7天
      if (filter.days) {
        const now = new Date();
        const daysAgo = new Date(now.getTime() - filter.days * 24 * 60 * 60 * 1000);
        return tweetDate >= daysAgo;
      }
    }
    
    // 如果是字符串，尝试解析为日期
    if (typeof filter === 'string') {
      try {
        const targetDate = new Date(filter);
        if (!isNaN(targetDate.getTime())) {
          // 如果只有日期，匹配整天
          const tweetDateStr = tweetDate.toISOString().split('T')[0];
          const targetDateStr = targetDate.toISOString().split('T')[0];
          return tweetDateStr === targetDateStr;
        }
      } catch (e) {
        console.log(`⚠️ 时间过滤器格式无效: ${filter}`);
      }
    }
    
    console.log(`⚠️ 不支持的时间过滤器格式: ${JSON.stringify(filter)}`);
    return false;
  }

  /**
   * 点击Following标签页
   */
  async clickFollowing() {
    try {
      console.log('👥 点击Following链接...');
      
      // 使用提供的xpath定位Following链接
      const followingXPath = '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]/div[1]/div/nav/div/div[2]/div/div[2]/a/div/div/span';
      
      // 等待元素出现
      await this.page.waitForXPath(followingXPath, { timeout: 10000 });
      
      // 点击Following链接
      const [followingElement] = await this.page.$x(followingXPath);
      if (followingElement) {
        await followingElement.click();
        console.log('✅ 成功点击Following链接');
      } else {
        throw new Error('未找到Following链接元素');
      }
      
      // 等待Following页面加载
      await this.page.waitForTimeout(3000);
      
    } catch (error) {
      console.error('❌ 点击Following链接失败:', error.message);
      console.log('🔍 尝试其他方式定位Following链接...');
      
      // 备用方案：通过文本内容查找
      try {
        await this.page.click('text=Following');
        console.log('✅ 通过文本成功点击Following链接');
        await this.page.waitForTimeout(3000);
      } catch (backupError) {
        console.error('❌ 备用方案也失败了:', backupError.message);
        throw error;
      }
    }
  }

  /**
   * 爬取Following页面的推文
   */
  async scrapeTweets(maxTweets = 10) {
    try {
      console.log(`📝 开始爬取Following页面推文 (最多 ${maxTweets} 条)...`);
      
      const tweets = [];
      let scrollAttempts = 0;
      const maxScrollAttempts = 10;
      
      while (tweets.length < maxTweets && scrollAttempts < maxScrollAttempts) {
        // 查找推文元素
        const tweetElements = await this.page.$$('article[data-testid="tweet"]');
        
        console.log(`🔍 当前页面找到 ${tweetElements.length} 条推文`);
        
        for (const tweetElement of tweetElements) {
          if (tweets.length >= maxTweets) break;
          
          try {
            const tweetData = await this.extractTweetData(tweetElement);
            
            // 调试信息：显示提取到的推文基本信息
            if (tweetData) {
              console.log(`🔍 提取推文: ID=${tweetData.id}, 时间戳=${tweetData.timestamp}, 用户=${tweetData.username}`);
            }
            
            // 检查推文是否已经爬取过
            if (tweetData && this.scrapedTweetIds.has(tweetData.id)) {
              console.log(`⏭️ 跳过重复推文: ${tweetData.id}`);
              continue;
            }
            
            // 检查推文年份是否符合要求
            if (tweetData && this.isTweetInTimeRange(tweetData.timestamp)) {
              if (!tweets.some(t => t.id === tweetData.id)) {
                tweets.push(tweetData);
                this.scrapedTweetIds.add(tweetData.id);
                
                const yearInfo = this.targetYear ? ` (${this.targetYear}年)` : '';
                console.log(`✅ 提取推文${yearInfo} ${tweets.length}/${maxTweets}: ${tweetData.text.substring(0, 50)}...`);
              }
            } else if (this.targetYear && tweetData && tweetData.timestamp) {
              console.log(`⏭️ 跳过非${this.targetYear}年推文: ${tweetData.text.substring(0, 30)}...`);
            }
          } catch (error) {
            console.log('⚠️ 跳过一条推文:', error.message);
          }
        }
        
        // 滚动加载更多推文
        if (tweets.length < maxTweets) {
          await this.page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
          });
          
          await this.page.waitForTimeout(2000);
          scrollAttempts++;
        }
      }
      
      console.log(`🎉 成功爬取 ${tweets.length} 条Following推文`);
      return tweets;
      
    } catch (error) {
      console.error('❌ 爬取推文失败:', error.message);
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
      
      // 提取时间 - 使用多种选择器尝试
      let timestamp = '';
      let timeElement = null;
      
      // 尝试多种时间选择器
      const timeSelectors = [
        'time',
        'time[datetime]',
        '[data-testid="Time"]',
        'a[href*="/status/"] time',
        'article time'
      ];
      
      for (const selector of timeSelectors) {
        timeElement = await tweetElement.$(selector);
        if (timeElement) {
          timestamp = await timeElement.getAttribute('datetime');
          if (timestamp) {
            break;
          }
        }
      }
      
      // 如果还是没有找到时间戳，尝试从链接中提取
      if (!timestamp) {
        const linkElement = await tweetElement.$('a[href*="/status/"]');
        if (linkElement) {
          const href = await linkElement.getAttribute('href');
          // 从推文链接中提取时间信息（如果有的话）
          console.log(`⚠️ 未找到时间戳，推文链接: ${href}`);
        } else {
          console.log(`⚠️ 未找到时间戳和推文链接，可能是广告`);
        }
      }
      
      // 提取推文链接
      const linkElement = await tweetElement.$('a[href*="/status/"]');
      const tweetUrl = linkElement ? await linkElement.getAttribute('href') : '';
      
      // 提取推文ID
      const tweetId = tweetUrl ? tweetUrl.split('/status/')[1]?.split('?')[0] : '';
      
      // 提取互动数据 - 扩展版本
      const replyElement = await tweetElement.$('[data-testid="reply"]');
      const retweetElement = await tweetElement.$('[data-testid="retweet"]');
      const likeElement = await tweetElement.$('[data-testid="like"]');
      const bookmarkElement = await tweetElement.$('[data-testid="bookmark"]');
      const shareElement = await tweetElement.$('[data-testid="share"]');
      
      // 尝试提取view数量 (浏览量) - 多种策略
      const viewSelectors = [
        'a[href*="/analytics"] span',
        '[data-testid="app-text-transition-container"]',
        'a[aria-label*="View"] span',
        'a[aria-label*="views"] span',
        'a[aria-label*="浏览"] span',
        '[role="link"][href*="analytics"] span'
      ];
      
      const replies = replyElement ? await this.extractCount(replyElement) : 0;
      const retweets = retweetElement ? await this.extractCount(retweetElement) : 0;
      const likes = likeElement ? await this.extractCount(likeElement) : 0;
      const bookmarks = bookmarkElement ? await this.extractCount(bookmarkElement) : 0;
      const shares = shareElement ? await this.extractCount(shareElement) : 0;
      
      // 提取view数量 - 使用多种选择器
      let views = 0;
      for (const selector of viewSelectors) {
        try {
          const viewElement = await tweetElement.$(selector);
          if (viewElement) {
            const viewCount = await this.extractCount(viewElement);
            if (viewCount > 0) {
              views = viewCount;
              break;
            }
          }
        } catch (error) {
          // 继续尝试下一个选择器
        }
      }
      
      console.log(`📊 完整互动数据 - 回复: ${replies}, 转推: ${retweets}, 点赞: ${likes}, 书签: ${bookmarks}, 分享: ${shares}, 浏览: ${views}`);
      
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
        bookmarks: bookmarks,
        shares: shares,
        views: views,
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
      // 尝试多种选择器来提取互动数量
      const selectors = [
        'span[data-testid*="count"]',
        'span',
        '[role="button"] span',
        'div span',
        '*'
      ];
      
      for (const selector of selectors) {
          const countElement = await element.$(selector);
          if (countElement) {
            const countText = await countElement.textContent();
            if (countText && countText.trim()) {
              const count = this.parseCount(countText);
              return count;
            }
          }
        }
       
       return 0;
    } catch (error) {
      console.log(`❌ 提取互动数量失败: ${error.message}`);
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
   * 保存推文数据
   */
  async saveTweets(tweets) {
    try {
      console.log(`🔧 准备保存 ${tweets.length} 条推文到结构化目录: ${this.structuredDir}`);
      
      // 创建结构化存储目录
      if (!fs.existsSync(this.structuredDir)) {
        console.log('📁 创建结构化存储目录...');
        fs.mkdirSync(this.structuredDir, { recursive: true });
      }
      
      // 同时保存传统格式（向后兼容）
      await this.saveTweetsLegacy(tweets);
      
      // 保存结构化格式
      await this.saveTweetsStructured(tweets);
      
    } catch (error) {
      console.error('❌ 保存推文数据失败:', error.message);
      console.error('❌ 错误详情:', error);
      throw error;
    }
  }

  /**
   * 保存传统JSON格式（向后兼容）
   */
  async saveTweetsLegacy(tweets) {
    try {
      if (!fs.existsSync(this.outputDir)) {
        fs.mkdirSync(this.outputDir, { recursive: true });
      }
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filterSuffix = this.getFilterSuffix();
      const filename = `following_tweets${filterSuffix}_${timestamp}.json`;
      const filepath = path.join(this.outputDir, filename);
      
      console.log(`💾 保存传统格式: ${filename}`);
      
      const jsonData = JSON.stringify(tweets, null, 2);
      fs.writeFileSync(filepath, jsonData, 'utf8');
      
      if (fs.existsSync(filepath)) {
        const stats = fs.statSync(filepath);
        console.log(`✅ 传统格式保存成功: ${stats.size} 字节`);
      }
      
    } catch (error) {
      console.error('❌ 传统格式保存失败:', error.message);
      throw error;
    }
  }

  /**
   * 保存结构化格式（每篇推文独立文件夹）
   */
  async saveTweetsStructured(tweets) {
    try {
      console.log(`📂 开始保存结构化格式...`);
      
      for (let i = 0; i < tweets.length; i++) {
        const tweet = tweets[i];
        await this.saveSingleTweetStructured(tweet, i + 1);
      }
      
      console.log(`✅ 结构化格式保存完成! 共处理 ${tweets.length} 条推文`);
      
    } catch (error) {
      console.error('❌ 结构化格式保存失败:', error.message);
      throw error;
    }
  }

  /**
   * 保存单条推文的结构化格式
   */
  async saveSingleTweetStructured(tweet, index) {
    try {
      // 创建推文文件夹 - 格式：博主_爬取时间
      const username = (tweet.username || '未知用户').replace(/[\\/:*?"<>|]/g, '_'); // 清理文件名非法字符
      const scrapeTime = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19); // YYYY-MM-DDTHH-MM-SS
      const folderName = `${username}_${scrapeTime}`;
      const tweetDir = path.join(this.structuredDir, folderName);
      
      if (!fs.existsSync(tweetDir)) {
        fs.mkdirSync(tweetDir, { recursive: true });
      }
      
      // 创建media文件夹
      const mediaDir = path.join(tweetDir, 'media');
      if (!fs.existsSync(mediaDir)) {
        fs.mkdirSync(mediaDir, { recursive: true });
      }
      
      // 生成content.md
      const contentMd = this.generateContentMarkdown(tweet);
      const contentPath = path.join(tweetDir, 'content.md');
      fs.writeFileSync(contentPath, contentMd, 'utf8');
      
      // 生成metadata.json
      const metadata = this.generateMetadata(tweet);
      const metadataPath = path.join(tweetDir, 'metadata.json');
      fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2), 'utf8');
      
      // 下载媒体文件（如果有）
      if (tweet.images && tweet.images.length > 0) {
        await this.downloadMediaFiles(tweet.images, mediaDir, folderName);
      }
      
      console.log(`📄 推文 ${folderName} 结构化保存完成`);
      
    } catch (error) {
      console.error(`❌ 推文 ${tweet.username || index} 结构化保存失败:`, error.message);
      // 不抛出错误，继续处理其他推文
    }
  }

  /**
   * 生成Markdown内容
   */
  generateContentMarkdown(tweet) {
    const timestamp = tweet.timestamp ? new Date(tweet.timestamp).toLocaleString('zh-CN') : '未知时间';
    
    return `# ${tweet.username || '未知用户'} 的推文

**发布时间**: ${timestamp}  
**用户**: ${tweet.username || '未知用户'} (${tweet.handle || '未知账号'})  
**推文ID**: ${tweet.id || '未知ID'}  
**链接**: [查看原推文](${tweet.url || '#'})

## 推文内容

${tweet.text || '无内容'}

## 互动数据

- 💬 回复: ${tweet.replies || 0}
- 🔄 转推: ${tweet.retweets || 0}
- ❤️ 点赞: ${tweet.likes || 0}
- 🔖 书签: ${tweet.bookmarks || 0}
- 📤 分享: ${tweet.shares || 0}
- 👁️ 浏览: ${tweet.views || 0}

## 媒体文件

${this.generateMediaMarkdown(tweet.images || [])}

---
*爬取时间: ${tweet.scraped_at ? new Date(tweet.scraped_at).toLocaleString('zh-CN') : '未知'}*
`;
  }

  /**
   * 生成媒体文件的Markdown
   */
  generateMediaMarkdown(images) {
    if (!images || images.length === 0) {
      return '无媒体文件';
    }
    
    return images.map((img, index) => {
      const filename = `image_${index + 1}.${this.getImageExtension(img)}`;
      return `![图片${index + 1}](./media/${filename})`;
    }).join('\n\n');
  }

  /**
   * 生成元数据JSON
   */
  generateMetadata(tweet) {
    return {
      id: tweet.id || null,
      text: tweet.text || '',
      username: tweet.username || '',
      handle: tweet.handle || '',
      timestamp: tweet.timestamp || null,
      url: tweet.url || '',
      engagement: {
        replies: tweet.replies || 0,
        retweets: tweet.retweets || 0,
        likes: tweet.likes || 0,
        bookmarks: tweet.bookmarks || 0,
        shares: tweet.shares || 0,
        views: tweet.views || 0
      },
      media: {
        images_count: (tweet.images || []).length,
        images_urls: tweet.images || []
      },
      scraped_at: tweet.scraped_at || new Date().toISOString(),
      filter_applied: this.timeFilter || null,
      source: 'X_Following_Scraper',
      version: '2.0'
    };
  }

  /**
   * 下载媒体文件
   */
  async downloadMediaFiles(imageUrls, mediaDir, tweetId) {
    try {
      console.log(`📥 开始下载 ${imageUrls.length} 个媒体文件...`);
      
      for (let i = 0; i < imageUrls.length; i++) {
        const imageUrl = imageUrls[i];
        if (!imageUrl || imageUrl.includes('profile_images')) {
          // 跳过头像图片
          continue;
        }
        
        try {
          const extension = this.getImageExtension(imageUrl);
          const filename = `image_${i + 1}.${extension}`;
          const filepath = path.join(mediaDir, filename);
          
          // 使用playwright下载图片
          if (this.page) {
            const response = await this.page.goto(imageUrl);
            if (response && response.ok()) {
              const buffer = await response.body();
              fs.writeFileSync(filepath, buffer);
              console.log(`✅ 下载成功: ${filename}`);
            }
          }
        } catch (downloadError) {
          console.warn(`⚠️ 下载图片失败: ${imageUrl}`, downloadError.message);
        }
      }
      
    } catch (error) {
      console.warn(`⚠️ 媒体文件下载过程出错:`, error.message);
    }
  }

  /**
   * 获取图片扩展名
   */
  getImageExtension(url) {
    if (!url) return 'jpg';
    
    if (url.includes('format=jpg') || url.includes('.jpg')) return 'jpg';
    if (url.includes('format=png') || url.includes('.png')) return 'png';
    if (url.includes('format=webp') || url.includes('.webp')) return 'webp';
    if (url.includes('format=gif') || url.includes('.gif')) return 'gif';
    
    return 'jpg'; // 默认
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
  async run(maxTweets = 10) {
    try {
      const filterInfo = this.timeFilter ? ` (时间过滤: ${JSON.stringify(this.timeFilter)})` : '';
      console.log(`🚀 开始爬取Following页面推文${filterInfo}...`);
      
      await this.initBrowser();
      await this.navigateToHome();
      await this.clickFollowing();
      
      const tweets = await this.scrapeTweets(maxTweets);
      await this.saveTweets(tweets);
      
      const filterDesc = this.getFilterDescription();
      console.log(`🎉 Following推文爬取完成! 共获取${filterDesc}推文 ${tweets.length} 条`);
      return tweets;
      
    } catch (error) {
      console.error('❌ 爬取过程中发生错误:', error.message);
      throw error;
    } finally {
      await this.close();
    }
  }

  /**
   * 获取过滤器描述文本
   */
  getFilterDescription() {
    if (!this.timeFilter) return '';
    
    if (typeof this.timeFilter === 'number') {
      return `${this.timeFilter}年`;
    }
    
    if (typeof this.timeFilter === 'string') {
      return `${this.timeFilter}的`;
    }
    
    if (typeof this.timeFilter === 'object') {
      if (this.timeFilter.startYear || this.timeFilter.endYear) {
        const start = this.timeFilter.startYear || '开始';
        const end = this.timeFilter.endYear || '结束';
        return `${start}-${end}年间的`;
      }
      
      if (this.timeFilter.startDate || this.timeFilter.endDate) {
        const start = this.timeFilter.startDate || '开始';
        const end = this.timeFilter.endDate || '结束';
        return `${start}到${end}期间的`;
      }
      
      if (this.timeFilter.days) {
        return `最近${this.timeFilter.days}天的`;
      }
    }
    
    return '过滤后的';
  }

  /**
   * 获取文件名后缀
   */
  getFilterSuffix() {
    if (!this.timeFilter) return '';
    
    if (typeof this.timeFilter === 'number') {
      return `_${this.timeFilter}`;
    }
    
    if (typeof this.timeFilter === 'string') {
      return `_${this.timeFilter.replace(/[^\w-]/g, '_')}`;
    }
    
    if (typeof this.timeFilter === 'object') {
      if (this.timeFilter.startYear || this.timeFilter.endYear) {
        const start = this.timeFilter.startYear || 'start';
        const end = this.timeFilter.endYear || 'end';
        return `_${start}-${end}`;
      }
      
      if (this.timeFilter.startDate || this.timeFilter.endDate) {
        const start = this.timeFilter.startDate ? this.timeFilter.startDate.replace(/[^\w-]/g, '_') : 'start';
        const end = this.timeFilter.endDate ? this.timeFilter.endDate.replace(/[^\w-]/g, '_') : 'end';
        return `_${start}_to_${end}`;
      }
      
      if (this.timeFilter.days) {
        return `_last${this.timeFilter.days}days`;
      }
    }
    
    return '_filtered';
  }
}

// 主程序入口
async function main() {
  const maxTweets = process.argv[2] ? parseInt(process.argv[2]) : 10;
  const timeFilterArg = process.argv[3];
  
  // 解析时间过滤器参数
  let timeFilter = null;
  if (timeFilterArg) {
    // 如果是纯数字，当作年份处理
    if (/^\d{4}$/.test(timeFilterArg)) {
      timeFilter = parseInt(timeFilterArg);
    }
    // 如果是日期格式，当作具体日期处理
    else if (/^\d{4}-\d{2}-\d{2}$/.test(timeFilterArg)) {
      timeFilter = timeFilterArg;
    }
    // 如果是JSON格式，尝试解析为对象
    else if (timeFilterArg.startsWith('{')) {
      try {
        timeFilter = JSON.parse(timeFilterArg);
      } catch (e) {
        console.error('❌ 时间过滤器JSON格式错误:', timeFilterArg);
        process.exit(1);
      }
    }
    // 其他格式尝试直接使用
    else {
      timeFilter = timeFilterArg;
    }
  }
  
  console.log('============================================================');
  console.log('🕷️  X Following页面推文爬虫');
  console.log('============================================================');
  console.log(`📊 最大爬取数量: ${maxTweets}`);
  if (timeFilter) {
    console.log(`⏰ 时间过滤器: ${JSON.stringify(timeFilter)}`);
  }
  console.log('============================================================');
  
  const scraper = new FollowingTweetsScraper(timeFilter);
  
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

module.exports = FollowingTweetsScraper;