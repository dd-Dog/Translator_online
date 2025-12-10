# test_comet_install.py
try:
    import comet
    print(f"✅ COMET版本: {comet.__version__}")
    
    # 测试基础功能
    from comet import download_model
    
    # 尝试下载一个小模型测试
    print("正在下载测试模型...")
    try:
        # 先用小模型测试
        model_path = download_model("Unbabel/wmt20-comet-da")
        print(f"✅ 模型下载成功: {model_path}")
    except Exception as e:
        print(f"⚠️ 模型下载可能有问题（网络或权限）: {e}")
        print("但COMET本身安装成功了！")
    
    print("\n🎉 COMET安装验证通过！")
    
except ImportError as e:
    print(f"❌ COMET导入失败: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")