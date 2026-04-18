import json
import openai
import chromadb
from pathlib import Path
import sys
import re
import time
from datetime import datetime


# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))
from config import Config

##########切割字符数量##########
MAX_LEN = 4000  # 安全阈值


def split_and_merge(paper):
    """将段落分割成适合模型处理的块"""
    if not paper:
        return []
    
    import re
    # 只匹配行首的单个 # （不匹配 ## 或 ###）
    paragraphs = re.split(r'(?=^#\s)', paper, flags=re.MULTILINE)
    
    result = []
    current = ""
    
    
    for p in paragraphs:
        if not p or not p.strip():
            continue
        
        if len(current) + len(p) <= MAX_LEN:
            current += p + "\n"
        else:
            if current:
                result.append(current)
            current = p + "\n"
    
    if current:
        result.append(current)
    
    return result


def split_and_merge(paper):
    """将段落分割成适合模型处理的块"""
    
    if not paper:
        return []
    
    # 先按 # 分割，再按句子分割
    paragraphs = paper.split('#')
    result = []
    current = ""
    
    for p in paragraphs:
        if not p or not p.strip():
            continue
        
        # 按句子分割段落
        sentences = re.split(r'(?<=[。！？；])', p)
        
        for sent in sentences:
            if not sent.strip():
                continue
            
            # 如果当前块加上这个句子会超过限制
            if len(current) + len(sent) > MAX_LEN:
                # 保存当前块
                if current:
                    result.append(current)
                    current = ""
                
                # 如果单个句子超过限制，按字符分割
                if len(sent) > MAX_LEN:
                    for i in range(0, len(sent), MAX_LEN):
                        chunk = sent[i:i+MAX_LEN]
                        if chunk.strip():
                            result.append(chunk)
                else:
                    current = sent
            else:
                current += sent
        
        # 段落结束后添加换行
        if current:
            current += "\n"
    
    # 添加最后一个块
    if current:
        result.append(current)
    
    # 过滤太小的块（降低阈值到20个字符）
    return [r for r in result if len(r.strip()) > 20]


class BasicRAG:
    """基础RAG检索器（单线程）"""
    
    def __init__(self):
        """初始化"""
        # 使用豆包 Embedding Large 的配置
        self.client = openai.OpenAI(
            api_key=Config.API_KEY,
            base_url=Config.BASE_URL
        )
        self.embedding_model = 'GLM-Embedding-3'
        
        # 连接向量数据库
        self.chroma_client = chromadb.PersistentClient(path="./vector_db")
        
        # 两个独立的Collection
        self.financial_collection = self.chroma_client.get_or_create_collection("financial_reports")
        self.research_collection = self.chroma_client.get_or_create_collection("research_reports")
        
        # 统计信息
        self.stats = {
            "total_chunks": 0,
            "success_chunks": 0,
            "failed_chunks": 0
        }
        
        print(f"初始化完成")
        print(f"  Embedding模型: {self.embedding_model}")
        print(f"  API Base URL: {Config.BASE_URL}")
        print(f"  财报库: {self.financial_collection.count()} 个文档")
        print(f"  研报库: {self.research_collection.count()} 个文档")
    
    def get_embedding(self, text: str, max_retries: int = 3) -> list:
        """调用API获取向量，带重试和错误处理"""
           
        # 限制文本长度（保守估计）
        if len(text) > MAX_LEN:
            text = text[:MAX_LEN]
        
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=[text],
                    dimensions=2048
                )
                return response.data[0].embedding
                
            except Exception as e:
                error_msg = str(e)
                
                # 如果是权重错误，不重试（输入内容问题）
                if "Total of weights must be greater than zero" in error_msg:
                    return None
                
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    time.sleep(wait_time)
                else:
                    return None
    
    def add_financial_report(self, file_path: str, metadata: dict) -> bool:
        """添加财报（单线程）"""
        file_path = Path(file_path)
        
        print(f"  📖 读取文件: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"  ❌ 读取文件失败: {e}")
            return False
        
        
        if not text:
            print(f"  ⚠️ 文件内容为空")
            return False
        
        chunks = split_and_merge(text)
        
        if not chunks:
            print(f"  ⚠️ 没有有效的文本块")
            return False
        
        total_chunks = len(chunks)
        print(f"  📦 分为 {total_chunks} 个文本块")
        
        # 准备基础元数据
        base_metadata = {
            "type": "financial",
            "source": file_path.name,
            **metadata
        }
        
        print(f"  🏷️ 元数据: {metadata}")
        
        # 更新统计
        self.stats["total_chunks"] += total_chunks
        
        # 单线程逐个处理
        success_count = 0
        print(f"  🔄 开始处理 {total_chunks} 个块...")
        
        for i, chunk in enumerate(chunks):
                     
            # 获取向量
            embedding = self.get_embedding(chunk)
            
            if embedding:
                # 清理 metadata
                meta = {}
                for key, value in base_metadata.items():
                    if value is not None and value != "":
                        meta[key] = value
                meta["chunk_index"] = i
                
                try:
                    self.financial_collection.add(
                        ids=[f"financial_{file_path.stem}_{i}"],
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[meta]
                    )
                    self.stats["success_chunks"] += 1
                    success_count += 1
                except Exception as e:
                    self.stats["failed_chunks"] += 1
                    print(f"    ❌ 块 {i} 添加失败: {e}")
            else:
                self.stats["failed_chunks"] += 1
            
            # 每处理10%打印进度
            if (i + 1) % max(1, total_chunks // 10) == 0 or (i + 1) == total_chunks:
                success_rate = success_count / (i + 1) * 100 if (i + 1) > 0 else 0
                print(f"    进度: {success_count}/{i+1} 成功 ({success_rate:.1f}%)")
        
        print(f"  ✅ 块处理完成: {success_count}/{total_chunks} 成功 ({success_count/total_chunks*100:.1f}%)")
        
        return success_count > 0
    
    def get_stats(self):
        """获取统计信息"""
        return {
            "financial_reports": self.financial_collection.count(),
            "research_reports": self.research_collection.count(),
            "total_chunks": self.stats["total_chunks"],
            "success_chunks": self.stats["success_chunks"],
            "failed_chunks": self.stats["failed_chunks"],
            "embedding_model": self.embedding_model
        }


def main():
    print("="*80)
    print("🚀 开始批量处理财报文件")
    print("="*80)
    
    # 初始化 RAG
    print("\n📌 初始化 RAG 系统...")
    rag = BasicRAG()
    
    # 获取所有财报文件
    reports_dir = Path(Path(__file__).parent.parent / 'processed' / '附件2：财务报告')
    files = list(reports_dir.rglob('*.md'))
    total_files = len(files)
    jsonpath = Path(__file__).parent.parent / 'task1' / 'output'
    
    print(f"\n📊 找到 {total_files} 个财报文件")
    print(f"📁 文件目录: {reports_dir}")
    print(f"📁 JSON目录: {jsonpath}")
    
    # 统计变量
    stats = {
        'success_files': 0,
        'fail_files': 0,
        'skip_files': 0
    }
    
    # 记录开始时间
    start_time = time.time()
    
    # 单线程逐个处理文件
    for idx, file in enumerate(files, 1):
        print(f"\n{'='*60}")
        print(f"[{idx}/{total_files}] 开始处理: {file.name}")
        print(f"{'='*60}")
        
        try:
            # 读取对应的 JSON 元数据
            json_file = jsonpath / str(file.name).replace('.md', '.json')
            
            if not json_file.exists():
                print(f"⚠️ 跳过 {file.name}: 找不到JSON文件 {json_file}")
                stats['skip_files'] += 1
                continue
            
            print(f"📋 读取元数据: {json_file.name}")
            
            with open(json_file, encoding='utf-8') as f:
                data = json.load(f).get('报告信息', {})
            
            if not data:
                print(f"⚠️ JSON数据为空")
                stats['skip_files'] += 1
                continue
            
            # 提取需要的字段
            keep_keys = ['股票代码', '股票简称', '报告年份', '报告期']
            filtered_data = {}
            for key in keep_keys:
                if key in data and data[key]:
                    filtered_data[key] = data[key]
            
            if not filtered_data:
                print(f"⚠️ 缺少必要字段，可用字段: {list(data.keys())}")
                stats['skip_files'] += 1
                continue
            
            print(f"✅ 提取元数据成功: {filtered_data}")
            
            # 添加到 RAG
            result = rag.add_financial_report(file, filtered_data)
            
            if result:
                stats['success_files'] += 1
                print(f"\n🎉 文件处理成功: {file.name}")
            else:
                stats['fail_files'] += 1
                print(f"\n❌ 文件处理失败: {file.name}")
                
        except Exception as e:
            print(f"\n💥 处理异常: {e}")
            stats['fail_files'] += 1
    
    # 计算耗时
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    
    # 最终统计
    print(f"\n{'='*80}")
    print(f"📊 处理完成!")
    print(f"{'='*80}")
    print(f"⏱️ 总耗时: {hours}小时 {minutes}分钟 {seconds}秒")
    print(f"\n📁 文件统计:")
    print(f"  总文件数: {total_files}")
    print(f"  ✅ 成功: {stats['success_files']}")
    print(f"  ❌ 失败: {stats['fail_files']}")
    print(f"  ⚠️ 跳过: {stats['skip_files']}")
    
    # 获取详细统计
    try:
        stats_detail = rag.get_stats()
        print(f"\n📦 块统计:")
        print(f"  总块数: {stats_detail['total_chunks']}")
        print(f"  ✅ 成功块: {stats_detail['success_chunks']}")
        print(f"  ❌ 失败块: {stats_detail['failed_chunks']}")
        if stats_detail['total_chunks'] > 0:
            success_rate = stats_detail['success_chunks']/stats_detail['total_chunks']*100
            print(f"  📈 成功率: {success_rate:.2f}%")
        
        print(f"\n💾 数据库统计:")
        print(f"  财报库文档数: {stats_detail['financial_reports']}")
        print(f"  研报库文档数: {stats_detail['research_reports']}")
    except Exception as e:
        print(f"获取详细统计失败: {e}")
    
    print(f"\n{'='*80}")
    print("🎉 批量处理完成!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
