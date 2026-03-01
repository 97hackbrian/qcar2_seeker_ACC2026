import torch

# Intentaremos importar onnx y onnxruntime si están instalados
try:
    import onnx
except ImportError:
    onnx = None

try:
    import onnxruntime
except ImportError:
    onnxruntime = None

def check_environment():
    print("=== PyTorch & CUDA / GPU Check ===")

    # Versión de PyTorch
    print(f"PyTorch version : {torch.__version__}")
    print(f"Compiled CUDA with PyTorch : {torch.version.cuda}")

    # Comprobar soporte CUDA
    cuda_available = torch.cuda.is_available()
    print(f"CUDA available : {cuda_available}")

    if cuda_available:
        # Cuántas GPUs detecta
        num_gpus = torch.cuda.device_count()
        print(f"Number of CUDA devices: {num_gpus}")
        for i in range(num_gpus):
            try:
                name = torch.cuda.get_device_name(i)
            except Exception as e:
                name = f"Error retrieving name: {e}"
            print(f" - GPU {i} : {name}")

        # Prueba mover un tensor a CUDA
        try:
            tensor = torch.randn(2, 2).to("cuda")
            print(f"Tensor successfully moved to : {tensor.device}")
        except Exception as e:
            print(f"Error moving tensor to GPU : {e}")

        # Información de memoria de GPU
        try:
            alloc = torch.cuda.memory_allocated(0) / (1024**2)
            reserved = torch.cuda.memory_reserved(0) / (1024**2)
            print(f"GPU memory usage (device 0): allocated {alloc:.2f} MB, reserved {reserved:.2f} MB")
        except Exception as e:
            print(f"Error reading GPU memory info : {e}")

    else:
        print("No CUDA-compatible GPU detected or PyTorch CUDA support not installed.")

    print("\n=== ONNX Check ===")
    if onnx:
        try:
            print(f"ONNX version : {onnx.__version__}")
        except AttributeError:
            print("ONNX installed but __version__ attribute not present (some builds may not expose it).")
    else:
        print("ONNX not installed or not importable.")

    print("\n=== ONNX Runtime Check ===")
    if onnxruntime:
        try:
            print(f"ONNX Runtime version : {onnxruntime.__version__}")
        except AttributeError:
            print("ONNX Runtime installed but __version__ attribute not present.")
    else:
        print("ONNX Runtime not installed or not importable.")

if __name__ == "__main__":
    check_environment()
