const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function loginWithCookies() {
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
      slowMo: 500 // 慢速执行，方便观察
    });
    
    const context = await browser.newContext();
    
    // 添加cookie到浏览器上下文
    await context.addCookies(cookies);
    console.log('Cookie已加载到浏览器');
    
    const page = await context.newPage();
    
    // 直接访问X主页，应该已经登录了
    console.log('正在访问X主页...');
    await page.goto('https://x.com/home');
    
    // 等待页面加载
    await page.waitForTimeout(3000);
    
    // 检查是否成功登录
    try {
      // 查找登录后才有的元素，比如发推文按钮
      await page.waitForSelector('[data-testid="SideNav_NewTweet_Button"]', { timeout: 5000 });
      console.log('🎉 成功！已使用cookie自动登录X！');
      console.log('浏览器将保持打开状态，你可以正常使用X了');
    } catch (error) {
      console.log('⚠️  可能需要重新登录，cookie可能已过期');
      console.log('请关闭浏览器，重新运行 login_x.js 获取新的cookie');
    }
    
    // 保持浏览器打开
    console.log('\n按Ctrl+C退出脚本并关闭浏览器');
    
    // 监听退出信号
    process.on('SIGINT', async () => {
      console.log('\n正在关闭浏览器...');
      await browser.close();
      process.exit(0);
    });
    
    // 保持脚本运行
    await new Promise(() => {});
    
  } catch (error) {
    console.error('使用cookie登录时出现错误:', error);
  }
}

loginWithCookies();

console.log('\n=== X自动登录脚本 ===');
console.log('此脚本将使用保存的cookie自动登录X');
console.log('如果登录失败，请重新运行 login_x.js 获取新cookie');
console.log('========================\n');