import subprocess
import modal

# --- 配置 ---
# 为 Modal 资源设置统一的名称，方便管理
VOLUME_NAME = "my-notebook-volume"
APP_NAME = "interactive-app"
APP_DIR = "/app"

# --- Modal App 设置 ---
app = modal.App(APP_NAME)

# 定义环境镜像，可以按需添加 apt 和 pip 包
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git")  # 必须先安装 git
    .pip_install(
        "pandas",
        "scikit-learn",
        "accelerate",
        "torch",
        "transformers==4.42.4",
        "xformers",
        "sentencepiece",
        "diffusers @ git+https://github.com/huggingface/diffusers.git",
    )
)

# 从统一名称创建或获取持久化存储卷
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)

# --- Modal 函数定义 ---

@app.function(
    image=image,
    volumes={APP_DIR: volume},
    gpu=modal.gpu.A100(),  # 请求 A100 GPU
    timeout=3600,  # 容器最长运行1小时
)
def run_command_in_container(command: str):
    """
    在容器内安全地执行终端命令。
    """
    print(f"准备执行命令: '{command}'")
    try:
        # 使用 shell=True 时要谨慎，这里我们信任用户输入的命令
        subprocess.run(command, shell=True, check=True, cwd=APP_DIR)
        print("\n命令执行成功。")
    except subprocess.CalledProcessError as e:
        print(f"\n命令执行失败: {e}")


# --- CLI 入口点 ---

@app.local_entrypoint()
def main(command: str):
    """
    本地入口函数，用于在容器中执行命令。

    使用方法:
    modal run notebook.py --command "your-command-here"
    """
    run_command_in_container.remote(command)
