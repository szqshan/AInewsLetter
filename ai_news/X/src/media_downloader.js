/**
 * 媒体文件下载模块
 * 负责下载推文中的图片和视频文件
 */

class MediaDownloader {
    constructor() {
        this.downloadQueue = [];
        this.downloadStats = {
            total: 0,
            success: 0,
            failed: 0
        };
    }

    /**
     * 下载推文的所有媒体文件
     * @param {Object} tweetData 推文数据
     * @param {string} basePath 基础保存路径
     */
    async downloadTweetMedia(tweetData, basePath) {
        console.log(`开始下载推文媒体文件: ${tweetData.author.username}`);
        
        // 直接在 crawled_data 下创建推文文件夹，不需要中间的 tweets 层
        const tweetFolder = `${basePath}/${tweetData.folderName}`;
        const mediaFolder = `${tweetFolder}/media`;
        
        // 创建推文文件夹和媒体子文件夹
        await this.createDirectory(tweetFolder);
        await this.createDirectory(mediaFolder);
        
        // 保存推文内容为 content.md
        await this.saveTweetContent(tweetData, tweetFolder);
        
        // 保存推文元数据为 metadata.json
        await this.saveTweetMetadata(tweetData, tweetFolder);
        
        // 下载图片到 media 文件夹
        if (tweetData.images && tweetData.images.length > 0) {
            await this.downloadImages(tweetData.images, mediaFolder);
        }
        
        // 下载视频到 media 文件夹
        if (tweetData.videos && tweetData.videos.length > 0) {
            await this.downloadVideos(tweetData.videos, mediaFolder);
        }
        
        console.log(`推文媒体文件下载完成: ${tweetData.folderName}`);
        return tweetFolder;
    }

    /**
     * 下载图片文件
     * @param {Array} images 图片数组
     * @param {string} imagePath 图片保存路径
     */
    async downloadImages(images, imagePath) {
        if (images.length === 0) return;
        
        console.log(`开始下载 ${images.length} 张图片...`);
        await this.createDirectory(imagePath);
        
        for (let i = 0; i < images.length; i++) {
            try {
                const image = images[i];
                const filename = `image_${i + 1}_${Date.now()}.jpg`;
                const filePath = `${imagePath}/${filename}`;
                
                await this.downloadFile(image.url, filePath);
                console.log(`图片下载成功: ${filename}`);
                this.downloadStats.success++;
                
            } catch (error) {
                console.error(`图片下载失败 ${i + 1}:`, error);
                this.downloadStats.failed++;
            }
        }
    }

    /**
     * 下载视频文件
     * @param {Array} videos 视频数组
     * @param {string} videoPath 视频保存路径
     */
    async downloadVideos(videos, videoPath) {
        if (videos.length === 0) return;
        
        console.log(`开始下载 ${videos.length} 个视频...`);
        await this.createDirectory(videoPath);
        
        for (let i = 0; i < videos.length; i++) {
            try {
                const video = videos[i];
                const filename = `video_${i + 1}_${Date.now()}.mp4`;
                const filePath = `${videoPath}/${filename}`;
                
                await this.downloadFile(video.url, filePath);
                console.log(`视频下载成功: ${filename}`);
                this.downloadStats.success++;
                
            } catch (error) {
                console.error(`视频下载失败 ${i + 1}:`, error);
                this.downloadStats.failed++;
            }
        }
    }

    /**
     * 下载单个文件
     * @param {string} url 文件URL
     * @param {string} filePath 保存路径
     */
    async downloadFile(url, filePath) {
        return new Promise((resolve, reject) => {
            // 在浏览器环境中，我们使用fetch下载文件
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.blob();
                })
                .then(blob => {
                    // 创建下载链接
                    const downloadUrl = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = downloadUrl;
                    link.download = filePath.split('/').pop(); // 获取文件名
                    
                    // 触发下载
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    // 清理URL对象
                    window.URL.revokeObjectURL(downloadUrl);
                    
                    this.downloadStats.total++;
                    resolve();
                })
                .catch(error => {
                    this.downloadStats.total++;
                    reject(error);
                });
        });
    }

    /**
     * 创建目录（浏览器环境中的模拟实现）
     * @param {string} dirPath 目录路径
     */
    async createDirectory(dirPath) {
        // 在浏览器环境中，我们无法直接创建文件夹
        // 这个方法主要用于记录目录结构
        console.log(`创建目录: ${dirPath}`);
        return Promise.resolve();
    }

    /**
     * 保存推文内容为 Markdown 文件
     * @param {Object} tweetData 推文数据
     * @param {string} tweetFolder 推文文件夹路径
     */
    async saveTweetContent(tweetData, tweetFolder) {
        const content = `# ${tweetData.author.displayName} (@${tweetData.author.username})

## 推文内容

${tweetData.text}

## 推文信息

- **发布时间**: ${tweetData.timestamp}
- **推文ID**: ${tweetData.id}
- **作者**: ${tweetData.author.displayName} (@${tweetData.author.username})
- **图片数量**: ${tweetData.images ? tweetData.images.length : 0}
- **视频数量**: ${tweetData.videos ? tweetData.videos.length : 0}

## 互动数据

- **回复**: ${tweetData.metrics.replies || 0}
- **转推**: ${tweetData.metrics.retweets || 0}
- **点赞**: ${tweetData.metrics.likes || 0}
- **书签**: ${tweetData.metrics.bookmarks || 0}

## 链接

${tweetData.links && tweetData.links.length > 0 ? tweetData.links.map(link => `- [${link.text || link.url}](${link.url})`).join('\n') : '无外部链接'}

---

*爬取时间: ${new Date().toISOString()}*
`;
        
        // 在浏览器环境中下载 Markdown 文件
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `content.md`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        window.URL.revokeObjectURL(url);
        
        console.log(`推文内容已保存: content.md`);
    }

    /**
     * 保存推文元数据
     * @param {Object} tweetData 推文数据
     * @param {string} tweetFolder 推文文件夹路径
     */
    async saveTweetMetadata(tweetData, tweetFolder) {
        const metadata = {
            id: tweetData.id,
            timestamp: tweetData.timestamp,
            author: tweetData.author,
            text: tweetData.text,
            metrics: tweetData.metrics,
            links: tweetData.links,
            downloadTime: new Date().toISOString(),
            downloadStats: {
                imagesCount: tweetData.images ? tweetData.images.length : 0,
                videosCount: tweetData.videos ? tweetData.videos.length : 0
            },
            folderName: tweetData.folderName
        };
        
        const jsonContent = JSON.stringify(metadata, null, 2);
        
        // 在浏览器环境中下载JSON文件
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `metadata.json`;
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        window.URL.revokeObjectURL(url);
        
        console.log(`推文元数据已保存: metadata.json`);
    }

    /**
     * 批量下载多条推文的媒体文件
     * @param {Array} tweetsData 推文数据数组
     * @param {string} basePath 基础保存路径
     */
    async downloadBatchMedia(tweetsData, basePath = 'crawled_data') {
        console.log(`开始批量下载 ${tweetsData.length} 条推文的媒体文件...`);
        
        const results = [];
        
        for (let i = 0; i < tweetsData.length; i++) {
            try {
                console.log(`处理推文 ${i + 1}/${tweetsData.length}`);
                const result = await this.downloadTweetMedia(tweetsData[i], basePath);
                results.push({ success: true, folder: result, tweet: tweetsData[i] });
                
                // 添加延迟避免请求过快
                await this.delay(1000);
                
            } catch (error) {
                console.error(`推文 ${i + 1} 下载失败:`, error);
                results.push({ success: false, error: error.message, tweet: tweetsData[i] });
            }
        }
        
        console.log('批量下载完成！');
        this.printDownloadSummary(results);
        
        return results;
    }

    /**
     * 打印下载摘要
     * @param {Array} results 下载结果数组
     */
    printDownloadSummary(results) {
        const successful = results.filter(r => r.success).length;
        const failed = results.filter(r => !r.success).length;
        
        console.log('\n=== 下载摘要 ===');
        console.log(`总推文数: ${results.length}`);
        console.log(`成功下载: ${successful}`);
        console.log(`下载失败: ${failed}`);
        console.log(`媒体文件统计:`);
        console.log(`  - 总文件数: ${this.downloadStats.total}`);
        console.log(`  - 成功下载: ${this.downloadStats.success}`);
        console.log(`  - 下载失败: ${this.downloadStats.failed}`);
        console.log('================\n');
    }

    /**
     * 延迟函数
     * @param {number} ms 延迟毫秒数
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 获取下载统计信息
     */
    getDownloadStats() {
        return { ...this.downloadStats };
    }

    /**
     * 重置下载统计
     */
    resetStats() {
        this.downloadStats = {
            total: 0,
            success: 0,
            failed: 0
        };
    }

    /**
     * 清理下载队列
     */
    clearQueue() {
        this.downloadQueue = [];
    }
}

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MediaDownloader;
} else {
    window.MediaDownloader = MediaDownloader;
}

console.log('媒体下载模块加载完成！');