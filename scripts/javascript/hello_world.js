// Chrome 书签测试脚本 - Hello World
// 这是一个简单的测试脚本示例

(function() {
    'use strict';

    console.log('='.repeat(50));
    console.log('Hello, Chrome 脚本管理器!');
    console.log('='.repeat(50));

    // 显示当前页面信息
    console.log('当前页面:', document.title);
    console.log('当前 URL:', document.location.href);

    // 创建一个简单的通知
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 999999;
        font-size: 14px;
    `;
    notification.innerHTML = `
        <div style="font-weight: bold;">脚本管理器测试</div>
        <div style="margin-top: 5px; font-size: 12px;">脚本执行成功!</div>
    `;
    document.body.appendChild(notification);

    // 3 秒后移除通知
    setTimeout(() => {
        setTimeout(() => notification.remove(), 300);
    }, 3000);

    console.log('脚本执行完成!');
    console.log('='.repeat(50));
})();
