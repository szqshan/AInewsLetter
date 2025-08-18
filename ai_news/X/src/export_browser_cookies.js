const fs = require('fs');
const path = require('path');

/**
 * 从本机浏览器手动导出Cookie的详细说明和验证工具
 * 无需额外依赖，支持所有主流浏览器
 */

class BrowserCookieHelper {
  constructor() {
    this.outputFile = path.join(__dirname, 'x_cookies.json');
  }

  /**
   * 显示详细的手动导出说明
   */
  showDetailedInstructions() {
    console.log('\n🎯 === 从本机浏览器导出X.com Cookie详细教程 === 🎯\n');
    
    console.log('📋 方法一：使用Cookie-Editor浏览器插件（推荐）\n');
    console.log('1️⃣ 安装Cookie-Editor插件：');
    console.log('   • Chrome: https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm');
    console.log('   • Firefox: https://addons.mozilla.org/firefox/addon/cookie-editor/');
    console.log('   • Edge: 在Edge扩展商店搜索"Cookie-Editor"\n');
    
    console.log('2️⃣ 导出步骤：');
    console.log('   a) 在浏览器中访问 https://x.com 并确保已登录');
    console.log('   b) 点击浏览器工具栏中的Cookie-Editor插件图标');
    console.log('   c) 在插件界面中点击"Export"按钮');
    console.log('   d) 选择"JSON"格式');
    console.log('   e) 复制导出的JSON内容\n');
    
    console.log('3️⃣ 保存Cookie：');
    console.log(`   将复制的JSON内容保存到文件: ${this.outputFile}\n`);
    
    console.log('📋 方法二：使用浏览器开发者工具\n');
    console.log('1️⃣ 在X.com页面按F12打开开发者工具');
    console.log('2️⃣ 切换到"Application"标签页（Chrome/Edge）或"存储"标签页（Firefox）');
    console.log('3️⃣ 在左侧找到"Cookies" -> "https://x.com"');
    console.log('4️⃣ 手动复制重要的Cookie值，格式如下：\n');
    
    this.showCookieTemplate();
    
    console.log('\n📋 方法三：使用浏览器控制台脚本\n');
    console.log('1️⃣ 在X.com页面按F12打开开发者工具');
    console.log('2️⃣ 切换到"Console"标签页');
    console.log('3️⃣ 复制并执行以下JavaScript代码：\n');
    
    this.showConsoleScript();
  }

  /**
   * 显示Cookie JSON模板
   */
  showCookieTemplate() {
    const template = [
      {
        "name": "auth_token",
        "value": "你的auth_token值",
        "domain": ".x.com",
        "path": "/"
      },
      {
        "name": "ct0",
        "value": "你的ct0值",
        "domain": ".x.com",
        "path": "/"
      },
      {
        "name": "twid",
        "value": "你的twid值",
        "domain": ".x.com",
        "path": "/"
      }
    ];
    
    console.log('Cookie JSON格式模板：');
    console.log(JSON.stringify(template, null, 2));
  }

  /**
   * 显示浏览器控制台脚本
   */
  showConsoleScript() {
    const script = `
// 在X.com页面的浏览器控制台中执行此脚本
function exportXCookies() {
  const cookies = document.cookie.split(';').map(cookie => {
    const [name, value] = cookie.trim().split('=');
    return {
      name: name,
      value: value || '',
      domain: '.x.com',
      path: '/'
    };
  }).filter(cookie => cookie.name && cookie.value);
  
  console.log('导出的Cookie JSON:');
  console.log(JSON.stringify(cookies, null, 2));
  
  // 复制到剪贴板（如果浏览器支持）
  if (navigator.clipboard) {
    navigator.clipboard.writeText(JSON.stringify(cookies, null, 2))
      .then(() => console.log('✅ Cookie已复制到剪贴板！'))
      .catch(() => console.log('⚠️ 请手动复制上面的JSON内容'));
  } else {
    console.log('⚠️ 请手动复制上面的JSON内容');
  }
  
  return cookies;
}

// 执行导出
exportXCookies();
    `;
    
    console.log(script);
  }

  /**
   * 验证Cookie文件
   */
  validateCookies() {
    console.log('\n🔍 验证Cookie文件...');
    
    if (!fs.existsSync(this.outputFile)) {
      console.log('❌ Cookie文件不存在:', this.outputFile);
      console.log('请先按照上述说明导出Cookie');
      return false;
    }
    
    try {
      const content = fs.readFileSync(this.outputFile, 'utf8');
      const cookies = JSON.parse(content);
      
      if (!Array.isArray(cookies)) {
        console.log('❌ Cookie文件格式错误：应该是JSON数组格式');
        return false;
      }
      
      if (cookies.length === 0) {
        console.log('❌ Cookie文件为空');
        return false;
      }
      
      // 检查Cookie格式
      const validCookies = cookies.filter(cookie => 
        cookie.name && cookie.value && 
        (cookie.domain || '').includes('x.com')
      );
      
      if (validCookies.length === 0) {
        console.log('❌ 未找到有效的X.com Cookie');
        return false;
      }
      
      // 检查关键Cookie
      const importantCookies = ['auth_token', 'ct0', 'twid', 'guest_id'];
      const foundImportant = importantCookies.filter(name => 
        cookies.some(cookie => cookie.name === name)
      );
      
      console.log(`✅ Cookie文件验证通过！`);
      console.log(`📊 总共 ${cookies.length} 个Cookie，其中 ${validCookies.length} 个X.com相关`);
      console.log(`🔑 找到重要Cookie: ${foundImportant.join(', ')}`);
      
      if (foundImportant.includes('auth_token') || foundImportant.includes('ct0')) {
        console.log('🎉 检测到登录状态Cookie，应该可以正常使用！');
      } else {
        console.log('⚠️ 未检测到登录状态Cookie，可能需要重新登录后导出');
      }
      
      return true;
      
    } catch (error) {
      console.log('❌ Cookie文件解析失败:', error.message);
      console.log('请检查JSON格式是否正确');
      return false;
    }
  }

  /**
   * 创建示例Cookie文件
   */
  createSampleFile() {
    const sampleCookies = [
      {
        "name": "guest_id",
        "value": "v1%3A123456789",
        "domain": ".x.com",
        "path": "/"
      },
      {
        "name": "ct0",
        "value": "请替换为真实的ct0值",
        "domain": ".x.com",
        "path": "/"
      },
      {
        "name": "auth_token",
        "value": "请替换为真实的auth_token值",
        "domain": ".x.com",
        "path": "/"
      }
    ];
    
    const sampleFile = this.outputFile.replace('.json', '_sample.json');
    fs.writeFileSync(sampleFile, JSON.stringify(sampleCookies, null, 2));
    
    console.log(`\n📝 已创建示例文件: ${sampleFile}`);
    console.log('请参考此文件格式，替换为真实的Cookie值');
  }

  /**
   * 显示使用说明
   */
  showUsage() {
    console.log('\n📖 使用说明：');
    console.log('node export_browser_cookies.js [选项]\n');
    console.log('选项：');
    console.log('  --help, -h     显示帮助信息');
    console.log('  --validate     验证现有Cookie文件');
    console.log('  --sample       创建示例Cookie文件');
    console.log('  --instructions 显示详细导出说明（默认）');
  }
}

// 主程序
function main() {
  const helper = new BrowserCookieHelper();
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.includes('-h')) {
    helper.showUsage();
  } else if (args.includes('--validate')) {
    helper.validateCookies();
  } else if (args.includes('--sample')) {
    helper.createSampleFile();
  } else {
    helper.showDetailedInstructions();
    console.log('\n💡 提示：');
    console.log('• 导出完成后运行: node export_browser_cookies.js --validate');
    console.log('• 需要示例文件: node export_browser_cookies.js --sample');
  }
}

if (require.main === module) {
  main();
}

module.exports = BrowserCookieHelper;