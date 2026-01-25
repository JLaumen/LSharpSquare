# Usage
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the main script:
   ```bash
   python run_benchmark.py -b "<oliveira|mealy>" [-t <timeout>] [-c] [-r]
    ```
    - `-b "<oliveira|mealy>"`: Specify the benchmark type, either "oliveira" or "mealy".
    - `-t <timeout>`: (Optional) Set a timeout value for the benchmark in seconds.
    - `-c`: (Optional) Use compatibility instead of apartness.
    - `-r`: (Optional) Use basis replacement.
   
   For example, to run the Oliveira benchmarks with a timeout of 200 seconds and with basis replacement, use:
   ```bash
   python run_benchmark.py -b "oliveira" -t 200 -r
   ```
    Note that the benchmarks will use all available CPU cores, so ensure your system can handle the load. The total
    expected time for the Oliveira benchmarks is approximately 10 to 20 CPU hours when using the default timeout of 200
    seconds, which can be divided by the number of available cores to estimate wall-clock time.
3. View the results:
    - The results of the Oliveira benchmarks will be saved to `benchmarking/results`.
    - The results of the Mealy benchmarks will be printed directly to the console. To save them to a file, you can
        redirect the output:
        ```bash
        python run_benchmark.py -b "mealy" > mealy_results.txt
        ```