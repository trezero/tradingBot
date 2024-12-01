import cupy as cp

try:
    # Print GPU info
    print("CUDA Version:", cp.cuda.runtime.runtimeGetVersion())
    print("Number of GPUs:", cp.cuda.runtime.getDeviceCount())
    print("GPU Name:", cp.cuda.runtime.getDeviceProperties(0)['name'])

    # Try a simple GPU computation
    x = cp.array([1, 2, 3])
    y = cp.array([4, 5, 6])
    z = cp.add(x, y)
    print("GPU Computation Test:", z)
    print("GPU Test Successful!")
except Exception as e:
    print("Error:", e)