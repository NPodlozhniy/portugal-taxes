# portugal-taxes
Portugal tax console calculator for 2023

## :zap: Getting started

The app support interaction via two approaches either a standard console or a docker container

### Installation

You can just copy the repo without installing any additional packages

```
$ git clone https://github.com/NPodlozhniy/portugal-taxes.git
$ cd portugal-taxes
```

### Usage

#### :black_large_square: Terminal

This way is suitable for users who already have Python installed

First of all you should install the dependencies as following
```
$ pip install --no-cache-dir -r requirements.txt
```
That's it, app is ready to use! By default calculator return Portugal taxes for an employee who lives on mainland Portugal
```
$ python main.py -a <YOUR INCOME>
```

If you want to specify a different residence option, you can view the help
```
$ python main.py --help
```

#### :whale: Docker

If you don't have Python installed this option is designed especially for you

Instead of using Python, build the container with the name `calculator`
```
docker build -t calculator .
```
And then you are all set! You can do all the things as described in the first part using `docker run --rm calculator` instead of `python main.py`
```
docker run --rm calculator -a <YOUR INCOME>
```

### :beers: Examples
```
$ python main.py -a -nr 15000
$ python main.py -ar Madeira 50000
$ python main.py 49506.00 --year 2024 -nhr Mainland -b 04/23 -e 344.16
$ python main.py 82813.28 --year 2024 -nhr Mainland -b 01/24 -e 2223.16
```
