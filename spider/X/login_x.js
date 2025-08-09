const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function saveCookies() {
  // 启动浏览器
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 // 慢速执行，方便观察
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log('正在导航到X登录页面...');
    await page.goto('https://x.com/login');
    
    // 等待页面加载
    await page.waitForTimeout(3000);
    
    console.log('页面已加载，请手动输入用户名和密码进行登录');
    console.log('登录完成后，按Enter键保存cookie并退出');
    
    // 等待用户按Enter键
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.on('data', async (key) => {
      if (key.toString() === '\r' || key.toString() === '\n') {
        console.log('\n正在保存cookie...');
        
        // 获取所有cookie
        const cookies = await context.cookies();
        
        // 保存cookie到文件
        const cookieFile = path.join(__dirname, 'x_cookies.json');
        fs.writeFileSync(cookieFile, JSON.stringify(cookies, null, 2));
        
        console.log(`Cookie已保存到: ${cookieFile}`);
        console.log(`共保存了 ${cookies.length} 个cookie`);
        
        // 关闭浏览器
        await browser.close();
        process.exit(0);
      }
    });
    
    // 保持浏览器打开，等待用户操作
    await page.waitForTimeout(600000); // 等待10分钟
    
  } catch (error) {
    console.error('保存cookie过程中出现错误:', error);
  } finally {
    await browser.close();
  }
}

saveCookies();