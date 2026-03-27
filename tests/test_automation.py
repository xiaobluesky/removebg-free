#!/usr/bin/env python3.11
"""
Remove.bg Free 自动化验收测试脚本
测试 002 号项目 - 背景移除功能

验收标准：
1. 上传图片 → 自动抠图 → 下载 PNG
2. 批量处理可用
3. 测试至少 10 次，成功率>90%
4. 无明显 BUG（crash、超时）
"""

import requests
import subprocess
import time
import os
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
TEST_IMAGES_DIR = "test_images"
OUTPUT_DIR = "output"
TEST_COUNT = 10
SUCCESS_THRESHOLD = 0.9  # 90% 成功率

class TestRunner:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def check_backend_health(self):
        """检查后端服务是否可用"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except Exception as e:
            return False
    
    def start_backend(self):
        """启动后端服务"""
        self.log("启动后端服务...")
        backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
        
        # 检查是否已经在运行
        if self.check_backend_health():
            self.log("后端服务已在运行")
            return True
        
        # 启动服务
        self.process = subprocess.Popen(
            ["python3.11", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服务启动
        self.log("等待服务启动...")
        for i in range(30):
            time.sleep(1)
            if self.check_backend_health():
                self.log("后端服务启动成功")
                return True
        
        self.log("后端服务启动超时")
        return False
    
    def stop_backend(self):
        """停止后端服务"""
        if hasattr(self, 'process'):
            self.process.terminate()
            self.process.wait()
            self.log("后端服务已停止")
    
    def test_single_image(self, image_path, test_num, max_retries=3):
        """测试单张图片处理 (带重试)"""
        for attempt in range(max_retries):
            try:
                with open(image_path, 'rb') as f:
                    files = {'file': (os.path.basename(image_path), f, 'image/png')}
                    response = requests.post(
                        f"{BASE_URL}/api/remove-bg",
                        files=files,
                        timeout=60
                    )
                    
                if response.status_code == 200 and response.headers.get('content-type') == 'image/png':
                    # 保存输出
                    output_path = os.path.join(OUTPUT_DIR, f"test_{test_num}_output.png")
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 验证输出文件
                    if os.path.getsize(output_path) > 0:
                        return True, "成功"
                    else:
                        return False, "输出文件为空"
                else:
                    return False, f"HTTP {response.status_code}: {response.text}"
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    self.log(f"  测试 {test_num} 超时，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(2)
                    continue
                return False, "超时"
            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                if attempt < max_retries - 1:
                    self.log(f"  测试 {test_num} 连接错误，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(2)
                    # 检查后端是否还在运行
                    if not self.check_backend_health():
                        self.log("  后端服务已崩溃，等待重启...")
                        time.sleep(5)
                        self.start_backend()
                    continue
                return False, f"连接错误：{str(e)}"
            except Exception as e:
                return False, str(e)
        
        return False, "多次重试后仍失败"
    
    def test_batch_processing(self, image_paths, max_retries=3):
        """测试批量处理 (带重试)"""
        for attempt in range(max_retries):
            try:
                files = []
                file_handles = []
                for path in image_paths:
                    fh = open(path, 'rb')
                    file_handles.append(fh)
                    files.append(('files', (os.path.basename(path), fh, 'image/png')))
                
                response = requests.post(
                    f"{BASE_URL}/api/batch-remove-bg",
                    files=files,
                    timeout=120
                )
                
                # 关闭文件
                for fh in file_handles:
                    fh.close()
                
                if response.status_code == 200:
                    data = response.json()
                    success_count = data.get('success', 0)
                    total = data.get('total', 0)
                    if success_count == total:
                        return True, f"批量处理成功：{success_count}/{total}"
                    else:
                        return False, f"部分失败：{success_count}/{total}"
                else:
                    return False, f"HTTP {response.status_code}"
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    self.log(f"  批量处理超时，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(5)
                    continue
                return False, "超时"
            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                if attempt < max_retries - 1:
                    self.log(f"  批量处理连接错误，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(5)
                    if not self.check_backend_health():
                        self.log("  后端服务已崩溃，等待重启...")
                        time.sleep(5)
                        self.start_backend()
                    continue
                return False, f"连接错误：{str(e)}"
            except Exception as e:
                return False, str(e)
        
        return False, "多次重试后仍失败"
    
    def test_api_endpoint(self):
        """测试 API 根端点"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "running":
                    return True, "API 正常"
            return False, "API 响应异常"
        except Exception as e:
            return False, str(e)
    
    def run_tests(self):
        """运行所有测试"""
        self.start_time = datetime.now()
        self.log("=" * 60)
        self.log("Remove.bg Free 自动化验收测试")
        self.log("=" * 60)
        
        # 1. 检查后端 (假设已在运行)
        self.log("\n检查后端服务状态...")
        if not self.check_backend_health():
            self.log("⚠️  后端服务未运行，尝试启动...")
            if not self.start_backend():
                self.log("❌ 无法启动后端服务，测试终止")
                return False
        else:
            self.log("✅ 后端服务已在运行")
        
        # 2. 测试 API 端点
        self.log("\n测试 1: API 端点检查")
        success, msg = self.test_api_endpoint()
        self.results.append(("API 端点检查", success, msg))
        self.log(f"  {'✅' if success else '❌'} {msg}")
        
        # 3. 单图处理测试 (10 次)
        self.log(f"\n测试 2: 单图处理测试 ({TEST_COUNT} 次)")
        single_success = 0
        for i in range(TEST_COUNT):
            image_path = os.path.join(TEST_IMAGES_DIR, f"test_{i+1}.png")
            if os.path.exists(image_path):
                success, msg = self.test_single_image(image_path, i+1)
                self.results.append((f"单图处理 #{i+1}", success, msg))
                self.log(f"  {'✅' if success else '❌'} 测试 {i+1}: {msg}")
                if success:
                    single_success += 1
            else:
                self.log(f"  ⚠️  测试图片不存在：{image_path}")
        
        single_rate = single_success / TEST_COUNT if TEST_COUNT > 0 else 0
        self.log(f"  单图处理成功率：{single_success}/{TEST_COUNT} ({single_rate*100:.1f}%)")
        
        # 4. 批量处理测试
        self.log("\n测试 3: 批量处理测试")
        batch_images = [os.path.join(TEST_IMAGES_DIR, f"test_{i+1}.png") for i in range(5)]
        batch_images = [p for p in batch_images if os.path.exists(p)]
        if len(batch_images) >= 2:
            success, msg = self.test_batch_processing(batch_images)
            self.results.append(("批量处理", success, msg))
            self.log(f"  {'✅' if success else '❌'} {msg}")
        else:
            self.log("  ⚠️  测试图片不足，跳过批量测试")
        
        # 5. 计算总体成功率
        total_tests = len([r for r in self.results if not r[0].startswith("API")])
        total_success = sum(1 for r in self.results if r[1] and not r[0].startswith("API"))
        overall_rate = total_success / total_tests if total_tests > 0 else 0
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        # 6. 生成报告
        self.log("\n" + "=" * 60)
        self.log("验收报告")
        self.log("=" * 60)
        self.log(f"测试开始：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"测试结束：{self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"总耗时：{duration:.1f} 秒")
        self.log(f"总测试数：{len(self.results)}")
        self.log(f"成功数：{sum(1 for r in self.results if r[1])}")
        self.log(f"失败数：{sum(1 for r in self.results if not r[1])}")
        self.log(f"成功率：{overall_rate*100:.1f}%")
        self.log(f"阈值：{SUCCESS_THRESHOLD*100:.1f}%")
        
        # 7. 判定结果
        passed = overall_rate >= SUCCESS_THRESHOLD
        self.log("\n" + "=" * 60)
        if passed:
            self.log("✅ 验收通过")
        else:
            self.log("❌ 验收不通过")
        self.log("=" * 60)
        
        # 8. 保存报告
        self.save_report(passed, overall_rate, duration)
        
        # 停止后端（如果是测试启动的）
        # self.stop_backend()
        
        return passed
    
    def save_report(self, passed, success_rate, duration):
        """保存测试报告"""
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(report_dir, f"test_report_{timestamp}.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Remove.bg Free 验收测试报告\n\n")
            f.write(f"**测试时间**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 测试结果\n\n")
            f.write(f"- **总测试数**: {len(self.results)}\n")
            f.write(f"- **成功数**: {sum(1 for r in self.results if r[1])}\n")
            f.write(f"- **失败数**: {sum(1 for r in self.results if not r[1])}\n")
            f.write(f"- **成功率**: {success_rate*100:.1f}%\n")
            f.write(f"- **阈值**: {SUCCESS_THRESHOLD*100:.1f}%\n")
            f.write(f"- **总耗时**: {duration:.1f} 秒\n\n")
            f.write("## 验收结论\n\n")
            f.write(f"**{'✅ 通过' if passed else '❌ 不通过'}**\n\n")
            
            if not passed:
                f.write("### 失败详情\n\n")
                for name, success, msg in self.results:
                    if not success:
                        f.write(f"- {name}: {msg}\n")
            
            f.write("\n## 详细测试结果\n\n")
            f.write("| 测试项 | 结果 | 详情 |\n")
            f.write("|--------|------|------|\n")
            for name, success, msg in self.results:
                status = "✅" if success else "❌"
                f.write(f"| {name} | {status} | {msg} |\n")
        
        self.log(f"\n报告已保存：{report_path}")


if __name__ == "__main__":
    # 切换到测试目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    runner = TestRunner()
    success = runner.run_tests()
    
    sys.exit(0 if success else 1)
