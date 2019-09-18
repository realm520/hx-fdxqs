# Full Decentrialized eXchange Query Service
Contract exchange query service for HyperExchange project.

# Dependency
* Run pip to install dependencies.
```
pip install -r requirements.txt
```

# Usage
* Init db
  ```
  flask db init
  flask db migrate
  flask db upgrade
  ```
* Start scan service
  ```
  flask scan_block --times=0 --kline=1
  ```
* Start debug service
  ```
  flask run
  ```
* Run test cases
  ```
  flask test
  ```
