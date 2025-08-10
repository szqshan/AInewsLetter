# X (Twitter) 爬虫技术文档

## 目标网站信息

- **网站名称**: X (原Twitter)
- **网站地址**: https://x.com (https://twitter.com)
- **网站类型**: 社交媒体平台
- **内容类型**: 推文、用户动态、AI相关讨论
- **更新频率**: 实时更新
- **语言**: 多语言（主要英文）
- **特点**: 实时性强、信息密度高、影响力大

## 爬虫方案概述

### 技术架构
- **爬虫类型**: 基于浏览器自动化的爬虫
- **主要技术**: Node.js + Puppeteer + JavaScript
- **数据格式**: JSON → 结构化推文数据
- **特色功能**: 登录状态维护、图片下载、实时监控

### 核心功能
1. **特定用户推文爬取**: 获取指定用户的最新推文
2. **AI相关内容筛选**: 专注于AI、科技相关推文
3. **多媒体内容处理**: 下载推文中的图片和视频
4. **登录状态管理**: 维护登录状态以获取更多内容
5. **实时监控**: 定期检查新推文
6. **数据结构化**: 提取推文的关键信息

## 爬取方式详解

### 1. X平台特点和挑战

#### 平台特点
```javascript
const X_PLATFORM_CONFIG = {
    base_url: 'https://x.com',
    api_endpoints: {
        user_timeline: '/i/api/graphql/{query_id}/UserTweets',
        tweet_detail: '/i/api/graphql/{query_id}/TweetDetail',
        search: '/i/api/graphql/{query_id}/SearchTimeline'
    },
    selectors: {
        tweet_container: '[data-testid="tweet"]',
        tweet_text: '[data-testid="tweetText"]',
        tweet_time: 'time',
        tweet_author: '[data-testid="User-Name"]',
        tweet_stats: '[role="group"]',
        tweet_images: '[data-testid="tweetPhoto"] img',
        tweet_videos: '[data-testid="videoPlayer"]',
        reply_count: '[data-testid="reply"]',
        retweet_count: '[data-testid="retweet"]',
        like_count: '[data-testid="like"]',
        view_count: '[data-testid="app-text-transition-container"]'
    },
    rate_limits: {
        requests_per_15min: 300,
        tweets_per_request: 20,
        delay_between_requests: 2000
    },
    anti_detection: {
        user_agents: [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ],
        viewport_sizes: [
            { width: 1920, height: 1080 },
            { width: 1366, height: 768 },
            { width: 1440, height: 900 }
        ]
    }
};
```

### 2. 主要爬虫实现

#### OpenAI推文爬虫
```javascript
const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class OpenAITweetScraper {
    constructor() {
        this.browser = null;
        this.page = null;
        this.cookies = null;
        this.userAgent = X_PLATFORM_CONFIG.anti_detection.user_agents[0];
    }

    async initialize() {
        console.log('Initializing OpenAI Tweet Scraper...');
        
        // 启动浏览器
        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        });

        this.page = await this.browser.newPage();
        
        // 设置用户代理和视口
        await this.page.setUserAgent(this.userAgent);
        await this.page.setViewport({ width: 1920, height: 1080 });
        
        // 加载cookies
        await this.loadCookies();
        
        console.log('Browser initialized successfully');
    }

    async loadCookies() {
        try {
            const cookiesPath = path.join(__dirname, 'x_cookies.json');
            const cookiesString = await fs.readFile(cookiesPath, 'utf8');
            this.cookies = JSON.parse(cookiesString);
            
            if (this.cookies && this.cookies.length > 0) {
                await this.page.setCookie(...this.cookies);
                console.log('Cookies loaded successfully');
            }
        } catch (error) {
            console.log('No cookies found or error loading cookies:', error.message);
        }
    }

    async saveCookies() {
        try {
            const cookies = await this.page.cookies();
            const cookiesPath = path.join(__dirname, 'x_cookies.json');
            await fs.writeFile(cookiesPath, JSON.stringify(cookies, null, 2));
            console.log('Cookies saved successfully');
        } catch (error) {
            console.error('Error saving cookies:', error);
        }
    }

    async navigateToProfile(username = 'OpenAI') {
        const profileUrl = `https://x.com/${username}`;
        console.log(`Navigating to ${profileUrl}...`);
        
        try {
            await this.page.goto(profileUrl, { 
                waitUntil: 'networkidle2',
                timeout: 30000 
            });
            
            // 等待页面加载
            await this.page.waitForTimeout(3000);
            
            // 检查是否需要登录
            const loginRequired = await this.page.$('[data-testid="loginButton"]');
            if (loginRequired) {
                console.log('Login required, but continuing with limited access...');
            }
            
            console.log('Successfully navigated to profile');
        } catch (error) {
            console.error('Error navigating to profile:', error);
            throw error;
        }
    }

    async scrapeLatestTweets(count = 5) {
        console.log(`Scraping latest ${count} tweets...`);
        
        try {
            // 等待推文容器加载
            await this.page.waitForSelector('[data-testid="tweet"]', { timeout: 15000 });
            
            const tweets = [];
            let attempts = 0;
            const maxAttempts = 10;
            
            while (tweets.length < count && attempts < maxAttempts) {
                // 获取当前页面的推文
                const pageTweets = await this.page.evaluate((targetCount) => {
                    const tweetElements = document.querySelectorAll('[data-testid="tweet"]');
                    const tweets = [];
                    
                    for (let i = 0; i < Math.min(tweetElements.length, targetCount); i++) {
                        const tweet = tweetElements[i];
                        
                        try {
                            // 提取推文文本
                            const textElement = tweet.querySelector('[data-testid="tweetText"]');
                            const text = textElement ? textElement.innerText.trim() : '';
                            
                            // 提取时间
                            const timeElement = tweet.querySelector('time');
                            const timestamp = timeElement ? timeElement.getAttribute('datetime') : '';
                            const timeText = timeElement ? timeElement.innerText : '';
                            
                            // 提取作者信息
                            const authorElement = tweet.querySelector('[data-testid="User-Name"]');
                            const authorName = authorElement ? authorElement.innerText.split('\n')[0] : '';
                            const authorHandle = authorElement ? authorElement.innerText.split('\n')[1] : '';
                            
                            // 提取统计数据
                            const statsElements = tweet.querySelectorAll('[role="group"] [data-testid]');
                            let replies = 0, retweets = 0, likes = 0, views = 0;
                            
                            statsElements.forEach(element => {
                                const testId = element.getAttribute('data-testid');
                                const text = element.innerText;
                                const number = parseInt(text.replace(/[^0-9]/g, '')) || 0;
                                
                                if (testId === 'reply') replies = number;
                                else if (testId === 'retweet') retweets = number;
                                else if (testId === 'like') likes = number;
                            });
                            
                            // 提取图片
                            const imageElements = tweet.querySelectorAll('[data-testid="tweetPhoto"] img');
                            const images = Array.from(imageElements).map(img => ({
                                url: img.src,
                                alt: img.alt || ''
                            }));
                            
                            // 提取推文链接
                            const linkElement = tweet.querySelector('a[href*="/status/"]');
                            const tweetUrl = linkElement ? 'https://x.com' + linkElement.getAttribute('href') : '';
                            
                            // 提取推文ID
                            const tweetId = tweetUrl ? tweetUrl.split('/status/')[1]?.split('?')[0] : '';
                            
                            if (text && tweetId) {
                                tweets.push({
                                    id: tweetId,
                                    text: text,
                                    author: {
                                        name: authorName,
                                        handle: authorHandle
                                    },
                                    timestamp: timestamp,
                                    timeText: timeText,
                                    url: tweetUrl,
                                    stats: {
                                        replies: replies,
                                        retweets: retweets,
                                        likes: likes,
                                        views: views
                                    },
                                    images: images,
                                    scraped_at: new Date().toISOString()
                                });
                            }
                        } catch (error) {
                            console.log('Error processing tweet:', error);
                        }
                    }
                    
                    return tweets;
                }, count);
                
                // 合并推文并去重
                for (const tweet of pageTweets) {
                    if (!tweets.find(t => t.id === tweet.id)) {
                        tweets.push(tweet);
                    }
                }
                
                // 如果还需要更多推文，滚动页面
                if (tweets.length < count) {
                    await this.page.evaluate(() => {
                        window.scrollTo(0, document.body.scrollHeight);
                    });
                    await this.page.waitForTimeout(2000);
                }
                
                attempts++;
            }
            
            console.log(`Successfully scraped ${tweets.length} tweets`);
            return tweets.slice(0, count);
            
        } catch (error) {
            console.error('Error scraping tweets:', error);
            return [];
        }
    }

    async downloadImages(tweets) {
        console.log('Downloading images from tweets...');
        
        const imagesDir = path.join(__dirname, 'images');
        
        // 确保图片目录存在
        try {
            await fs.access(imagesDir);
        } catch {
            await fs.mkdir(imagesDir, { recursive: true });
        }
        
        for (const tweet of tweets) {
            if (tweet.images && tweet.images.length > 0) {
                console.log(`Downloading ${tweet.images.length} images for tweet ${tweet.id}`);
                
                for (let i = 0; i < tweet.images.length; i++) {
                    const image = tweet.images[i];
                    try {
                        const response = await this.page.goto(image.url);
                        const buffer = await response.buffer();
                        
                        const extension = image.url.includes('.jpg') ? '.jpg' : 
                                        image.url.includes('.png') ? '.png' : '.jpg';
                        const filename = `${tweet.id}_${i + 1}${extension}`;
                        const filepath = path.join(imagesDir, filename);
                        
                        await fs.writeFile(filepath, buffer);
                        
                        // 更新推文中的图片路径
                        tweet.images[i].local_path = filepath;
                        
                        console.log(`Downloaded: ${filename}`);
                    } catch (error) {
                        console.error(`Error downloading image ${image.url}:`, error);
                    }
                }
            }
        }
    }

    async saveResults(tweets, filename = 'openai_latest_tweets.json') {
        try {
            const filepath = path.join(__dirname, filename);
            await fs.writeFile(filepath, JSON.stringify(tweets, null, 2));
            console.log(`Results saved to ${filepath}`);
            
            // 同时保存Markdown格式
            const mdFilename = filename.replace('.json', '.md');
            const mdContent = this.generateMarkdownReport(tweets);
            await fs.writeFile(path.join(__dirname, mdFilename), mdContent);
            console.log(`Markdown report saved to ${mdFilename}`);
            
        } catch (error) {
            console.error('Error saving results:', error);
        }
    }

    generateMarkdownReport(tweets) {
        let markdown = `# OpenAI Latest Tweets\n\n`;
        markdown += `Generated on: ${new Date().toLocaleString()}\n\n`;
        markdown += `Total tweets: ${tweets.length}\n\n`;
        
        tweets.forEach((tweet, index) => {
            markdown += `## Tweet ${index + 1}\n\n`;
            markdown += `**Author:** ${tweet.author.name} (${tweet.author.handle})\n\n`;
            markdown += `**Time:** ${tweet.timeText}\n\n`;
            markdown += `**Content:**\n${tweet.text}\n\n`;
            
            if (tweet.images && tweet.images.length > 0) {
                markdown += `**Images:** ${tweet.images.length} image(s)\n\n`;
            }
            
            markdown += `**Stats:**\n`;
            markdown += `- Replies: ${tweet.stats.replies}\n`;
            markdown += `- Retweets: ${tweet.stats.retweets}\n`;
            markdown += `- Likes: ${tweet.stats.likes}\n\n`;
            
            markdown += `**URL:** [View Tweet](${tweet.url})\n\n`;
            markdown += `---\n\n`;
        });
        
        return markdown;
    }

    async close() {
        if (this.browser) {
            await this.saveCookies();
            await this.browser.close();
            console.log('Browser closed');
        }
    }
}

// 使用示例
async function scrapeOpenAITweets() {
    const scraper = new OpenAITweetScraper();
    
    try {
        await scraper.initialize();
        await scraper.navigateToProfile('OpenAI');
        
        const tweets = await scraper.scrapeLatestTweets(5);
        
        if (tweets.length > 0) {
            await scraper.downloadImages(tweets);
            await scraper.saveResults(tweets, 'openai_latest_5_tweets.json');
            
            console.log('\n=== SCRAPING COMPLETED ===');
            console.log(`Successfully scraped ${tweets.length} tweets`);
            
            tweets.forEach((tweet, index) => {
                console.log(`\nTweet ${index + 1}:`);
                console.log(`Text: ${tweet.text.substring(0, 100)}...`);
                console.log(`Likes: ${tweet.stats.likes}, Retweets: ${tweet.stats.retweets}`);
            });
        } else {
            console.log('No tweets found');
        }
        
    } catch (error) {
        console.error('Scraping failed:', error);
    } finally {
        await scraper.close();
    }
}

module.exports = { OpenAITweetScraper, scrapeOpenAITweets };
```

#### Elon Musk推文爬虫
```javascript
class ElonMuskTweetScraper extends OpenAITweetScraper {
    constructor() {
        super();
        this.targetUser = 'elonmusk';
    }

    async scrapeElonTweets(count = 10) {
        console.log(`Scraping latest ${count} tweets from Elon Musk...`);
        
        await this.navigateToProfile(this.targetUser);
        const tweets = await this.scrapeLatestTweets(count);
        
        // 过滤AI相关推文
        const aiRelatedTweets = this.filterAIRelatedTweets(tweets);
        
        return {
            all_tweets: tweets,
            ai_related: aiRelatedTweets
        };
    }

    filterAIRelatedTweets(tweets) {
        const aiKeywords = [
            'ai', 'artificial intelligence', 'machine learning', 'neural',
            'grok', 'xai', 'autopilot', 'fsd', 'tesla ai', 'neuralink',
            'robot', 'automation', 'algorithm', 'deep learning'
        ];
        
        return tweets.filter(tweet => {
            const text = tweet.text.toLowerCase();
            return aiKeywords.some(keyword => text.includes(keyword));
        });
    }
}
```

### 3. 登录状态管理

#### Cookie管理器
```javascript
class XCookieManager {
    constructor(cookiePath = './x_cookies.json') {
        this.cookiePath = cookiePath;
    }

    async saveCookies(page) {
        try {
            const cookies = await page.cookies();
            await fs.writeFile(this.cookiePath, JSON.stringify(cookies, null, 2));
            console.log('Cookies saved successfully');
        } catch (error) {
            console.error('Error saving cookies:', error);
        }
    }

    async loadCookies(page) {
        try {
            const cookiesString = await fs.readFile(this.cookiePath, 'utf8');
            const cookies = JSON.parse(cookiesString);
            
            if (cookies && cookies.length > 0) {
                await page.setCookie(...cookies);
                console.log('Cookies loaded successfully');
                return true;
            }
        } catch (error) {
            console.log('No cookies found or error loading cookies');
        }
        return false;
    }

    async isLoggedIn(page) {
        try {
            await page.goto('https://x.com/home', { waitUntil: 'networkidle2' });
            
            // 检查是否存在登录按钮
            const loginButton = await page.$('[data-testid="loginButton"]');
            return !loginButton;
        } catch (error) {
            return false;
        }
    }
}
```

### 4. 图片下载器

```javascript
class ImageDownloader {
    constructor(downloadDir = './images') {
        this.downloadDir = downloadDir;
    }

    async ensureDirectory() {
        try {
            await fs.access(this.downloadDir);
        } catch {
            await fs.mkdir(this.downloadDir, { recursive: true });
        }
    }

    async downloadTweetImages(page, tweets) {
        await this.ensureDirectory();
        
        for (const tweet of tweets) {
            if (tweet.images && tweet.images.length > 0) {
                console.log(`Downloading ${tweet.images.length} images for tweet ${tweet.id}`);
                
                for (let i = 0; i < tweet.images.length; i++) {
                    const image = tweet.images[i];
                    await this.downloadSingleImage(page, image, tweet.id, i + 1);
                }
            }
        }
    }

    async downloadSingleImage(page, image, tweetId, index) {
        try {
            // 获取高质量图片URL
            const highQualityUrl = image.url.replace(/&name=\w+/, '&name=large');
            
            const response = await page.goto(highQualityUrl);
            const buffer = await response.buffer();
            
            const extension = this.getImageExtension(highQualityUrl);
            const filename = `${tweetId}_${index}${extension}`;
            const filepath = path.join(this.downloadDir, filename);
            
            await fs.writeFile(filepath, buffer);
            
            // 更新图片信息
            image.local_path = filepath;
            image.filename = filename;
            
            console.log(`Downloaded: ${filename}`);
        } catch (error) {
            console.error(`Error downloading image ${image.url}:`, error);
        }
    }

    getImageExtension(url) {
        if (url.includes('.jpg') || url.includes('format=jpg')) return '.jpg';
        if (url.includes('.png') || url.includes('format=png')) return '.png';
        if (url.includes('.gif') || url.includes('format=gif')) return '.gif';
        if (url.includes('.webp') || url.includes('format=webp')) return '.webp';
        return '.jpg'; // 默认
    }
}
```

## 反爬虫应对策略

### 1. 浏览器指纹管理
```javascript
class AntiDetectionManager {
    static async setupPage(page) {
        // 隐藏webdriver属性
        await page.evaluateOnNewDocument(() => {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        });

        // 模拟真实浏览器环境
        await page.evaluateOnNewDocument(() => {
            window.chrome = {
                runtime: {},
            };
        });

        // 随机化视口大小
        const viewports = [
            { width: 1920, height: 1080 },
            { width: 1366, height: 768 },
            { width: 1440, height: 900 }
        ];
        const viewport = viewports[Math.floor(Math.random() * viewports.length)];
        await page.setViewport(viewport);

        // 设置随机User-Agent
        const userAgents = X_PLATFORM_CONFIG.anti_detection.user_agents;
        const userAgent = userAgents[Math.floor(Math.random() * userAgents.length)];
        await page.setUserAgent(userAgent);
    }

    static async randomDelay(min = 1000, max = 3000) {
        const delay = Math.floor(Math.random() * (max - min + 1)) + min;
        await new Promise(resolve => setTimeout(resolve, delay));
    }

    static async humanLikeScroll(page) {
        // 模拟人类滚动行为
        const scrollSteps = Math.floor(Math.random() * 5) + 3;
        
        for (let i = 0; i < scrollSteps; i++) {
            await page.evaluate(() => {
                window.scrollBy(0, Math.floor(Math.random() * 300) + 200);
            });
            await this.randomDelay(500, 1500);
        }
    }
}
```

### 2. 请求频率控制
```javascript
class RateLimiter {
    constructor(requestsPerMinute = 30) {
        this.requestsPerMinute = requestsPerMinute;
        this.requests = [];
    }

    async waitIfNeeded() {
        const now = Date.now();
        const oneMinuteAgo = now - 60000;
        
        // 清理一分钟前的请求记录
        this.requests = this.requests.filter(time => time > oneMinuteAgo);
        
        // 如果请求过多，等待
        if (this.requests.length >= this.requestsPerMinute) {
            const oldestRequest = Math.min(...this.requests);
            const waitTime = oldestRequest + 60000 - now;
            
            if (waitTime > 0) {
                console.log(`Rate limit reached, waiting ${waitTime}ms...`);
                await new Promise(resolve => setTimeout(resolve, waitTime));
            }
        }
        
        this.requests.push(now);
    }
}
```

## 配置参数

### 爬虫配置
```javascript
const X_SCRAPER_CONFIG = {
    browser_settings: {
        headless: true,
        timeout: 30000,
        viewport: { width: 1920, height: 1080 },
        user_data_dir: './user_data'
    },
    scraping_settings: {
        max_tweets_per_user: 50,
        include_images: true,
        include_videos: false,
        download_media: true,
        delay_between_requests: 2000
    },
    target_users: {
        ai_influencers: ['OpenAI', 'elonmusk', 'AndrewYNg', 'ylecun'],
        ai_companies: ['OpenAI', 'DeepMind', 'huggingface', 'AnthropicAI'],
        ai_researchers: ['karpathy', 'goodfellow_ian', 'ylecun']
    },
    content_filters: {
        ai_keywords: [
            'ai', 'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'gpt', 'llm', 'transformer', 'chatbot',
            'computer vision', 'nlp', 'robotics', 'automation'
        ],
        exclude_keywords: ['spam', 'advertisement', 'promotion'],
        min_engagement: 10
    }
};
```

## 数据输出格式

### JSON格式
```json
{
  "id": "1234567890123456789",
  "text": "Excited to announce our latest AI breakthrough...",
  "author": {
    "name": "OpenAI",
    "handle": "@OpenAI",
    "verified": true
  },
  "timestamp": "2024-01-15T12:00:00.000Z",
  "timeText": "2h",
  "url": "https://x.com/OpenAI/status/1234567890123456789",
  "stats": {
    "replies": 245,
    "retweets": 1250,
    "likes": 3420,
    "views": 125000
  },
  "images": [
    {
      "url": "https://pbs.twimg.com/media/example.jpg",
      "alt": "AI model architecture diagram",
      "local_path": "./images/1234567890123456789_1.jpg",
      "filename": "1234567890123456789_1.jpg"
    }
  ],
  "hashtags": ["#AI", "#MachineLearning", "#OpenAI"],
  "mentions": ["@elonmusk", "@karpathy"],
  "links": [
    {
      "url": "https://openai.com/blog/new-model",
      "display_url": "openai.com/blog/new-model"
    }
  ],
  "thread_info": {
    "is_thread": false,
    "thread_position": 1,
    "total_tweets": 1
  },
  "ai_relevance": {
    "score": 0.95,
    "keywords_found": ["AI", "machine learning", "neural network"],
    "category": "product_announcement"
  },
  "scraped_at": "2024-01-15T14:30:00.000Z",
  "scraper_version": "1.0"
}
```

## 常见问题与解决方案

### 1. 登录状态丢失
**问题**: Cookie过期导致无法访问完整内容
**解决**: 
- 定期更新Cookie
- 实现自动登录机制
- 监控登录状态

### 2. 反爬虫检测
**问题**: 被识别为机器人导致访问受限
**解决**: 
- 模拟真实用户行为
- 随机化请求间隔
- 使用代理IP轮换

### 3. 页面结构变化
**问题**: X平台频繁更新页面结构
**解决**: 
- 使用多重选择器备选
- 定期更新选择器
- 实现自适应解析

### 4. 图片下载失败
**问题**: 图片链接失效或下载超时
**解决**: 
- 实现重试机制
- 使用高质量图片链接
- 异步下载优化

## 维护建议

### 定期维护任务
1. **选择器更新**: 监控页面结构变化
2. **Cookie刷新**: 定期更新登录状态
3. **反检测优化**: 更新反爬虫策略
4. **数据质量检查**: 验证爬取数据的准确性

### 扩展方向
1. **实时监控**: 实现推文实时监控和推送
2. **情感分析**: 分析推文情感倾向
3. **影响力分析**: 评估推文传播影响力
4. **多语言支持**: 支持多语言推文处理

## 相关资源

- [X (Twitter)](https://x.com/)
- [Puppeteer Documentation](https://pptr.dev/)
- [Node.js Documentation](https://nodejs.org/docs/)
- [X Developer Platform](https://developer.x.com/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)