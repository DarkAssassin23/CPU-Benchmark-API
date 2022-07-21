# CPU Benchmark API

About
---------
A python script to pull CPU benchmarks, as well as other data about the CPU, from [cpubenchmark.net](https://cpubenchmark.net)

Setup
---------
**Optional**: If you want to run this in a virtual python environment
to prevent having more python packages than you need installed on 
your system, you can set up a virtual python environment with the 
following commands: 
```
python -m venv env
```
Then, for Windows users:
```
env/bin/activate.bat
```
For macOS and Linux users:
```
source env/bin/activate
```
**Required:** Install the required python packages with the 
following command:
```
pip install -r requirements.txt
```

If you modified the script and added additional libraries, and 
used a virtual environment, you can easily update the 
requirements.txt file with the following command:
```
pip freeze > requirements.txt
```
Once you're done in the python enviornment, you can exit it with the following command:
```
deactivate
```
------
Usage
------
Before you run the script, make sure you have a cpus.txt file.
That file should look something like this:
```
Intel Xeon X5650 @ 2.67GHZ&cpuCount=2
Intel Core i7-6920HQ @ 2.90GHz
Intel Core i9-9900K @ 3.60GHz
Intel Xeon E5-2670 v2 @ 2.50GHz
```

**Note:** the ```&cpuCount=2``` if you are trying to pull data from  
a dual or quad CPU set up, you must have this. Otherwise, you'll just 
get the single CPU results. You also don't need to specify the 
clockspeed, as denoted with the ```@ x.xxGHz```; however, you could 
get unexpected results if there are multiple variaties of the same 
cpu. For example, non-K vs K variants, like the i7-3770 vs i7-3770k, 
or V2/V3/V4 variants in server CPUs like the E5-2670 vs E5-2670 v3.
In my testing, for example, if I just entered i7-3770 I would get the 
i7-3770K back instead. I'd only get the i7-3770 if I added the 
clock speed

**TL;DR:** The more verbose you are about the cpu the more likely 
you'll be to get the one you want/expect

To run the script use the following command:
```
./cpubenchmarkapi.py
```
or 
```
python cpubenchmarkapi.py
```

Additionally, you can specify your own input and output files by 
tacking on -i and/or -o flags, respectfully, this will tell the script 
to use those rather than the default ```cpus.txt``` and 
```cpuData.csv``` as seen here:
```
./cpubenchmarkapi.py -i serverCPUs.txt -o serverCPUsData.csv
```
