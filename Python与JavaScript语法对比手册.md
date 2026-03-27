# Python 与 JavaScript 语法对比手册

## 目录
1. [基础语法](#基础语法)
2. [变量与数据类型](#变量与数据类型)
3. [运算符](#运算符)
4. [控制流](#控制流)
5. [函数](#函数)
6. [面向对象](#面向对象)
7. [模块与导入](#模块与导入)
8. [异步编程](#异步编程)
9. [常用内置函数/方法](#常用内置函数方法)
10. [Python 常用标准库 API](#python-常用标准库-api)

---

## 基础语法

### 注释

**Python:**
```python
# 单行注释

"""
多行注释
可以使用三引号
"""

'''
也可以使用单引号
'''
```

**JavaScript:**
```javascript
// 单行注释

/*
多行注释
使用斜杠星号
*/
```

### 代码块

**Python:**
```python
# 使用缩进（通常是4个空格）来定义代码块
if True:
    print("缩进表示代码块")
    print("同一缩进级别")
```

**JavaScript:**
```javascript
// 使用花括号 {} 来定义代码块
if (true) {
    console.log("花括号表示代码块");
    console.log("同一代码块");
}
```

### 语句结束

**Python:**
```python
# 不需要分号，换行即表示语句结束
x = 10
y = 20
```

**JavaScript:**
```javascript
// 分号可选但推荐使用
let x = 10;
let y = 20;
```

---

## 变量与数据类型

### 变量声明

**Python:**
```python
# 动态类型，不需要声明类型
x = 10              # 整数
name = "Alice"      # 字符串
is_valid = True     # 布尔值

# 类型注解（可选，用于类型检查）
age: int = 25
username: str = "Bob"
```

**JavaScript:**
```javascript
// var - 函数作用域（不推荐）
var x = 10;

// let - 块作用域，可重新赋值
let name = "Alice";
name = "Bob";

// const - 块作用域，不可重新赋值（但对象内容可变）
const PI = 3.14;
const user = { name: "Alice" };
user.name = "Bob";  // 允许
```

### 基本数据类型

**Python:**
```python
# 数字类型
integer = 42                    # 整数
floating = 3.14                 # 浮点数
complex_num = 3 + 4j            # 复数

# 字符串
single = 'Hello'                # 单引号
double = "World"                # 双引号
multi = """多行
字符串"""                        # 三引号

# 布尔值
is_true = True                  # 注意首字母大写
is_false = False

# None（空值）
nothing = None

# 类型转换
str(42)         # "42" - 转换为字符串
int("42")       # 42 - 转换为整数
float("3.14")   # 3.14 - 转换为浮点数
bool(1)         # True - 转换为布尔值
```

**JavaScript:**
```javascript
// 数字类型（只有一种 Number 类型）
let integer = 42;
let floating = 3.14;
let bigInt = 9007199254740991n;  // BigInt 用于大整数

// 字符串
let single = 'Hello';
let double = "World";
let template = `Hello ${name}`;  // 模板字符串，支持插值

// 布尔值
let isTrue = true;               // 注意小写
let isFalse = false;

// null 和 undefined
let nothing = null;              // 明确的空值
let notDefined = undefined;      // 未定义

// Symbol（ES6+）
let sym = Symbol('description');

// 类型转换
String(42)      // "42" - 转换为字符串
Number("42")    // 42 - 转换为数字
Boolean(1)      // true - 转换为布尔值
parseInt("42")  // 42 - 解析整数
parseFloat("3.14")  // 3.14 - 解析浮点数
```

### 字符串操作

**Python:**
```python
s = "Hello World"

# 字符串拼接
result = "Hello" + " " + "World"        # "Hello World"
result = f"Hello {name}"                # f-string 格式化（Python 3.6+）
result = "Hello {}".format(name)        # format 方法

# 字符串方法
s.lower()           # "hello world" - 转小写
s.upper()           # "HELLO WORLD" - 转大写
s.strip()           # 去除首尾空白
s.split()           # ['Hello', 'World'] - 分割字符串
s.replace("World", "Python")  # "Hello Python" - 替换
s.startswith("Hello")  # True - 检查开头
s.endswith("World")    # True - 检查结尾
s.find("World")        # 6 - 查找子串位置（找不到返回-1）
s.index("World")       # 6 - 查找子串位置（找不到抛异常）
len(s)                 # 11 - 字符串长度
s[0]                   # "H" - 索引访问
s[0:5]                 # "Hello" - 切片
s[::-1]                # "dlroW olleH" - 反转字符串
```

**JavaScript:**
```javascript
let s = "Hello World";

// 字符串拼接
let result = "Hello" + " " + "World";   // "Hello World"
let result = `Hello ${name}`;           // 模板字符串

// 字符串方法
s.toLowerCase()     // "hello world" - 转小写
s.toUpperCase()     // "HELLO WORLD" - 转大写
s.trim()            // 去除首尾空白
s.split(" ")        // ['Hello', 'World'] - 分割字符串
s.replace("World", "JavaScript")  // "Hello JavaScript" - 替换
s.startsWith("Hello")  // true - 检查开头
s.endsWith("World")    // true - 检查结尾
s.indexOf("World")     // 6 - 查找子串位置（找不到返回-1）
s.includes("World")    // true - 检查是否包含
s.length               // 11 - 字符串长度
s[0]                   // "H" - 索引访问
s.substring(0, 5)      // "Hello" - 提取子串
s.slice(0, 5)          // "Hello" - 切片
s.split("").reverse().join("")  // "dlroW olleH" - 反转字符串
```

### 列表/数组

**Python:**
```python
# 列表（List）- 可变、有序
fruits = ["apple", "banana", "cherry"]

# 列表操作
fruits.append("orange")      # 末尾添加元素
fruits.insert(1, "grape")    # 指定位置插入
fruits.remove("banana")      # 删除指定元素
fruits.pop()                 # 删除并返回最后一个元素
fruits.pop(0)                # 删除并返回指定索引元素
fruits.clear()               # 清空列表
fruits.sort()                # 原地排序
fruits.reverse()             # 原地反转
len(fruits)                  # 列表长度
fruits[0]                    # 索引访问
fruits[1:3]                  # 切片
fruits[-1]                   # 倒数第一个元素
"apple" in fruits            # 检查元素是否存在

# 列表推导式
squares = [x**2 for x in range(10)]  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
evens = [x for x in range(10) if x % 2 == 0]  # [0, 2, 4, 6, 8]
```

**JavaScript:**
```javascript
// 数组（Array）
let fruits = ["apple", "banana", "cherry"];

// 数组操作
fruits.push("orange")        // 末尾添加元素
fruits.unshift("grape")      // 开头添加元素
fruits.splice(1, 0, "kiwi")  // 指定位置插入
fruits.pop()                 // 删除并返回最后一个元素
fruits.shift()               // 删除并返回第一个元素
fruits.splice(1, 1)          // 删除指定位置元素
fruits = []                  // 清空数组
fruits.sort()                // 原地排序
fruits.reverse()             // 原地反转
fruits.length                // 数组长度
fruits[0]                    // 索引访问
fruits.slice(1, 3)           // 切片（不修改原数组）
fruits[fruits.length - 1]    // 最后一个元素
fruits.includes("apple")     // 检查元素是否存在

// 数组方法（函数式编程）
fruits.map(x => x.toUpperCase())     // 映射转换
fruits.filter(x => x.length > 5)     // 过滤
fruits.reduce((sum, x) => sum + x.length, 0)  // 归约
fruits.forEach(x => console.log(x))  // 遍历
fruits.find(x => x.startsWith("a"))  // 查找第一个匹配
fruits.some(x => x.length > 5)       // 是否有元素满足条件
fruits.every(x => x.length > 0)      // 是否所有元素满足条件

// 数组推导（使用 map/filter）
let squares = Array.from({length: 10}, (_, i) => i**2);
let evens = Array.from({length: 10}, (_, i) => i).filter(x => x % 2 === 0);
```

### 字典/对象

**Python:**
```python
# 字典（Dictionary）- 键值对
person = {
    "name": "Alice",
    "age": 25,
    "city": "Beijing"
}

# 字典操作
person["name"]              # "Alice" - 访问值
person.get("name")          # "Alice" - 安全访问（不存在返回None）
person.get("email", "N/A")  # "N/A" - 提供默认值
person["email"] = "alice@example.com"  # 添加/修改键值对
del person["age"]           # 删除键值对
person.pop("city")          # 删除并返回值
person.keys()               # 获取所有键
person.values()             # 获取所有值
person.items()              # 获取所有键值对
len(person)                 # 字典长度
"name" in person            # 检查键是否存在
person.update({"age": 26})  # 更新字典

# 字典推导式
squares = {x: x**2 for x in range(5)}  # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
```

**JavaScript:**
```javascript
// 对象（Object）
let person = {
    name: "Alice",
    age: 25,
    city: "Beijing"
};

// 对象操作
person.name                 // "Alice" - 点号访问
person["name"]              // "Alice" - 括号访问
person.email = "alice@example.com"  // 添加/修改属性
delete person.age           // 删除属性
Object.keys(person)         // 获取所有键
Object.values(person)       // 获取所有值
Object.entries(person)      // 获取所有键值对数组
Object.keys(person).length  // 对象属性数量
"name" in person            // 检查属性是否存在
person.hasOwnProperty("name")  // 检查自有属性
Object.assign(person, {age: 26})  // 合并对象

// ES6+ 特性
const {name, age} = person;  // 解构赋值
const newPerson = {...person, age: 26};  // 展开运算符（浅拷贝）

// Map（ES6+）- 更强大的键值对结构
let map = new Map();
map.set("name", "Alice");
map.get("name");            // "Alice"
map.has("name");            // true
map.delete("name");
map.size;                   // 大小
```

### 集合

**Python:**
```python
# 集合（Set）- 无序、不重复
numbers = {1, 2, 3, 4, 5}
empty_set = set()  # 注意：{} 是空字典

# 集合操作
numbers.add(6)              # 添加元素
numbers.remove(3)           # 删除元素（不存在会报错）
numbers.discard(3)          # 删除元素（不存在不报错）
numbers.clear()             # 清空集合
len(numbers)                # 集合大小
3 in numbers                # 检查元素是否存在

# 集合运算
a = {1, 2, 3}
b = {3, 4, 5}
a | b                       # {1, 2, 3, 4, 5} - 并集
a & b                       # {3} - 交集
a - b                       # {1, 2} - 差集
a ^ b                       # {1, 2, 4, 5} - 对称差集
```

**JavaScript:**
```javascript
// Set（ES6+）
let numbers = new Set([1, 2, 3, 4, 5]);

// 集合操作
numbers.add(6);             // 添加元素
numbers.delete(3);          // 删除元素
numbers.clear();            // 清空集合
numbers.size;               // 集合大小
numbers.has(3);             // 检查元素是否存在

// 集合运算（需要手动实现）
let a = new Set([1, 2, 3]);
let b = new Set([3, 4, 5]);
let union = new Set([...a, ...b]);              // 并集
let intersection = new Set([...a].filter(x => b.has(x)));  // 交集
let difference = new Set([...a].filter(x => !b.has(x)));   // 差集
```

---

## 运算符

### 算术运算符

**Python:**
```python
a + b       # 加法
a - b       # 减法
a * b       # 乘法
a / b       # 除法（结果为浮点数）
a // b      # 整除（向下取整）
a % b       # 取模（余数）
a ** b      # 幂运算
-a          # 取负
abs(a)      # 绝对值
```

**JavaScript:**
```javascript
a + b       // 加法
a - b       // 减法
a * b       // 乘法
a / b       // 除法
a % b       // 取模（余数）
a ** b      // 幂运算（ES7+）
-a          // 取负
Math.abs(a) // 绝对值
Math.floor(a / b)  // 整除
```

### 比较运算符

**Python:**
```python
a == b      # 等于
a != b      # 不等于
a > b       # 大于
a < b       # 小于
a >= b      # 大于等于
a <= b      # 小于等于
a is b      # 身份比较（同一对象）
a is not b  # 身份不同
```

**JavaScript:**
```javascript
a == b      // 相等（类型转换）
a === b     // 严格相等（不转换类型，推荐）
a != b      // 不等（类型转换）
a !== b     // 严格不等（不转换类型，推荐）
a > b       // 大于
a < b       // 小于
a >= b      // 大于等于
a <= b      // 小于等于
```

### 逻辑运算符

**Python:**
```python
a and b     # 逻辑与
a or b      # 逻辑或
not a       # 逻辑非
```

**JavaScript:**
```javascript
a && b      // 逻辑与
a || b      // 逻辑或
!a          // 逻辑非
a ?? b      // 空值合并运算符（ES2020+，a为null/undefined时返回b）
```

### 赋值运算符

**Python:**
```python
a = 10      # 赋值
a += 5      # a = a + 5
a -= 5      # a = a - 5
a *= 5      # a = a * 5
a /= 5      # a = a / 5
a //= 5     # a = a // 5
a %= 5      # a = a % 5
a **= 5     # a = a ** 5
```

**JavaScript:**
```javascript
let a = 10; // 赋值
a += 5;     // a = a + 5
a -= 5;     // a = a - 5
a *= 5;     // a = a * 5
a /= 5;     // a = a / 5
a %= 5;     // a = a % 5
a **= 5;    // a = a ** 5
a++;        // a = a + 1（后置递增）
++a;        // a = a + 1（前置递增）
a--;        // a = a - 1（后置递减）
--a;        // a = a - 1（前置递减）
```

---

## 控制流

### 条件语句

**Python:**
```python
# if-elif-else
if x > 0:
    print("正数")
elif x < 0:
    print("负数")
else:
    print("零")

# 三元运算符
result = "正数" if x > 0 else "非正数"

# match-case（Python 3.10+）
match status:
    case 200:
        print("成功")
    case 404:
        print("未找到")
    case _:
        print("其他")
```

**JavaScript:**
```javascript
// if-else if-else
if (x > 0) {
    console.log("正数");
} else if (x < 0) {
    console.log("负数");
} else {
    console.log("零");
}

// 三元运算符
let result = x > 0 ? "正数" : "非正数";

// switch-case
switch (status) {
    case 200:
        console.log("成功");
        break;
    case 404:
        console.log("未找到");
        break;
    default:
        console.log("其他");
}
```

### 循环语句

**Python:**
```python
# for 循环
for i in range(5):          # 0, 1, 2, 3, 4
    print(i)

for i in range(1, 6):       # 1, 2, 3, 4, 5
    print(i)

for i in range(0, 10, 2):   # 0, 2, 4, 6, 8（步长为2）
    print(i)

for item in items:          # 遍历列表
    print(item)

for index, item in enumerate(items):  # 带索引遍历
    print(f"{index}: {item}")

for key, value in dict.items():  # 遍历字典
    print(f"{key}: {value}")

# while 循环
while x < 10:
    print(x)
    x += 1

# 循环控制
break       # 跳出循环
continue    # 跳过本次迭代
else:       # for/while 循环正常结束时执行（没有break）
    print("循环完成")
```

**JavaScript:**
```javascript
// for 循环
for (let i = 0; i < 5; i++) {
    console.log(i);
}

// for...of 循环（遍历可迭代对象）
for (let item of items) {
    console.log(item);
}

// for...in 循环（遍历对象属性）
for (let key in obj) {
    console.log(key, obj[key]);
}

// forEach 方法
items.forEach((item, index) => {
    console.log(`${index}: ${item}`);
});

// while 循环
while (x < 10) {
    console.log(x);
    x++;
}

// do-while 循环（至少执行一次）
do {
    console.log(x);
    x++;
} while (x < 10);

// 循环控制
break;      // 跳出循环
continue;   // 跳过本次迭代
```

### 异常处理

**Python:**
```python
# try-except-else-finally
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
else:
    print("没有异常时执行")
finally:
    print("总是执行")

# 抛出异常
raise ValueError("无效的值")

# 自定义异常
class CustomError(Exception):
    pass

raise CustomError("自定义错误")
```

**JavaScript:**
```javascript
// try-catch-finally
try {
    let result = 10 / 0;  // JavaScript 中不会抛出异常，返回 Infinity
    throw new Error("手动抛出错误");
} catch (error) {
    console.log(`错误: ${error.message}`);
} finally {
    console.log("总是执行");
}

// 抛出异常
throw new Error("错误信息");

// 自定义异常
class CustomError extends Error {
    constructor(message) {
        super(message);
        this.name = "CustomError";
    }
}

throw new CustomError("自定义错误");
```

---

## 函数

### 函数定义

**Python:**
```python
# 基本函数
def greet(name):
    """函数文档字符串"""
    return f"Hello, {name}"

# 默认参数
def greet(name="World"):
    return f"Hello, {name}"

# 多个返回值
def get_user():
    return "Alice", 25  # 返回元组

name, age = get_user()  # 解包

# 可变参数
def sum_all(*args):     # *args 接收任意数量位置参数（元组）
    return sum(args)

def print_info(**kwargs):  # **kwargs 接收任意数量关键字参数（字典）
    for key, value in kwargs.items():
        print(f"{key}: {value}")

# Lambda 函数（匿名函数）
square = lambda x: x ** 2
add = lambda x, y: x + y

# 高阶函数
def apply(func, value):
    return func(value)

result = apply(lambda x: x * 2, 5)  # 10
```

**JavaScript:**
```javascript
// 函数声明
function greet(name) {
    return `Hello, ${name}`;
}

// 函数表达式
const greet = function(name) {
    return `Hello, ${name}`;
};

// 箭头函数（ES6+）
const greet = (name) => {
    return `Hello, ${name}`;
};

// 简写箭头函数（单表达式）
const greet = name => `Hello, ${name}`;

// 默认参数
function greet(name = "World") {
    return `Hello, ${name}`;
}

// 多个返回值（使用数组或对象）
function getUser() {
    return ["Alice", 25];  // 或 {name: "Alice", age: 25}
}

const [name, age] = getUser();  // 解构

// 剩余参数（ES6+）
function sumAll(...args) {      // ...args 接收任意数量参数（数组）
    return args.reduce((sum, x) => sum + x, 0);
}

// 高阶函数
function apply(func, value) {
    return func(value);
}

const result = apply(x => x * 2, 5);  // 10
```

### 作用域与闭包

**Python:**
```python
# 全局变量
global_var = "全局"

def outer():
    outer_var = "外部"
    
    def inner():
        # 访问外部变量
        print(outer_var)
        
        # 修改外部变量需要 nonlocal
        nonlocal outer_var
        outer_var = "修改后"
        
        # 修改全局变量需要 global
        global global_var
        global_var = "修改后"
    
    inner()
    return inner  # 返回闭包

# 闭包示例
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

counter = make_counter()
print(counter())  # 1
print(counter())  # 2
```

**JavaScript:**
```javascript
// 全局变量
let globalVar = "全局";

function outer() {
    let outerVar = "外部";
    
    function inner() {
        // 可以直接访问和修改外部变量
        console.log(outerVar);
        outerVar = "修改后";
        
        // 可以直接访问和修改全局变量
        globalVar = "修改后";
    }
    
    inner();
    return inner;  // 返回闭包
}

// 闭包示例
function makeCounter() {
    let count = 0;
    return function() {
        count++;
        return count;
    };
}

const counter = makeCounter();
console.log(counter());  // 1
console.log(counter());  // 2
```

---

## 面向对象

### 类定义

**Python:**
```python
# 类定义
class Person:
    # 类变量（所有实例共享）
    species = "Human"
    
    # 构造函数
    def __init__(self, name, age):
        # 实例变量
        self.name = name
        self.age = age
        self._private = "私有属性"  # 约定：单下划线表示私有
    
    # 实例方法
    def greet(self):
        return f"Hello, I'm {self.name}"
    
    # 类方法
    @classmethod
    def from_birth_year(cls, name, birth_year):
        age = 2024 - birth_year
        return cls(name, age)
    
    # 静态方法
    @staticmethod
    def is_adult(age):
        return age >= 18
    
    # 属性装饰器（getter）
    @property
    def info(self):
        return f"{self.name}, {self.age}"
    
    # setter
    @info.setter
    def info(self, value):
        name, age = value.split(", ")
        self.name = name
        self.age = int(age)
    
    # 特殊方法
    def __str__(self):
        return f"Person({self.name}, {self.age})"
    
    def __repr__(self):
        return f"Person(name='{self.name}', age={self.age})"

# 创建实例
person = Person("Alice", 25)
print(person.greet())
print(Person.is_adult(25))

# 继承
class Student(Person):
    def __init__(self, name, age, student_id):
        super().__init__(name, age)  # 调用父类构造函数
        self.student_id = student_id
    
    # 方法重写
    def greet(self):
        return f"Hi, I'm student {self.name}"

student = Student("Bob", 20, "S001")
```

**JavaScript:**
```javascript
// 类定义（ES6+）
class Person {
    // 静态属性
    static species = "Human";
    
    // 构造函数
    constructor(name, age) {
        // 实例属性
        this.name = name;
        this.age = age;
        this._private = "私有属性";  // 约定：下划线表示私有
    }
    
    // 实例方法
    greet() {
        return `Hello, I'm ${this.name}`;
    }
    
    // 静态方法
    static isAdult(age) {
        return age >= 18;
    }
    
    // Getter
    get info() {
        return `${this.name}, ${this.age}`;
    }
    
    // Setter
    set info(value) {
        const [name, age] = value.split(", ");
        this.name = name;
        this.age = parseInt(age);
    }
    
    // toString 方法
    toString() {
        return `Person(${this.name}, ${this.age})`;
    }
}

// 创建实例
const person = new Person("Alice", 25);
console.log(person.greet());
console.log(Person.isAdult(25));

// 继承
class Student extends Person {
    constructor(name, age, studentId) {
        super(name, age);  // 调用父类构造函数
        this.studentId = studentId;
    }
    
    // 方法重写
    greet() {
        return `Hi, I'm student ${this.name}`;
    }
}

const student = new Student("Bob", 20, "S001");

// 私有字段（ES2022+）
class BankAccount {
    #balance = 0;  // 真正的私有字段
    
    deposit(amount) {
        this.#balance += amount;
    }
    
    getBalance() {
        return this.#balance;
    }
}
```

---

## 模块与导入

### 模块系统

**Python:**
```python
# 导入整个模块
import math
print(math.sqrt(16))

# 导入特定函数/类
from math import sqrt, pi
print(sqrt(16))

# 导入并重命名
import numpy as np
from math import sqrt as square_root

# 导入所有（不推荐）
from math import *

# 相对导入
from .module import function      # 同级目录
from ..module import function     # 上级目录
from .subpackage.module import function  # 子包

# 导出（在模块中定义即可导出）
# mymodule.py
def my_function():
    pass

class MyClass:
    pass

# 使用 __all__ 控制 from module import * 的行为
__all__ = ['my_function', 'MyClass']
```

**JavaScript:**
```javascript
// ES6 模块（推荐）

// 导入默认导出
import React from 'react';

// 导入命名导出
import { useState, useEffect } from 'react';

// 导入并重命名
import { useState as useStateHook } from 'react';

// 导入所有
import * as React from 'react';

// 混合导入
import React, { useState } from 'react';

// 动态导入
const module = await import('./module.js');

// 导出
// mymodule.js

// 命名导出
export function myFunction() {}
export class MyClass {}
export const myVariable = 42;

// 默认导出（每个模块只能有一个）
export default function() {}
// 或
export default class MyClass {}

// 重新导出
export { myFunction } from './other-module.js';
export * from './other-module.js';

// CommonJS（Node.js 传统方式）
const fs = require('fs');
const { readFile } = require('fs');

module.exports = {
    myFunction,
    MyClass
};
```

---

## 异步编程

### 异步处理

**Python:**
```python
# async/await（Python 3.5+）
import asyncio

# 定义异步函数
async def fetch_data():
    await asyncio.sleep(1)  # 模拟异步操作
    return "数据"

# 调用异步函数
async def main():
    result = await fetch_data()
    print(result)
    
    # 并发执行多个异步任务
    results = await asyncio.gather(
        fetch_data(),
        fetch_data(),
        fetch_data()
    )

# 运行异步函数
asyncio.run(main())

# 使用 asyncio 创建任务
async def main():
    task1 = asyncio.create_task(fetch_data())
    task2 = asyncio.create_task(fetch_data())
    
    result1 = await task1
    result2 = await task2
```

**JavaScript:**
```javascript
// Promise
function fetchData() {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            resolve("数据");
        }, 1000);
    });
}

// 使用 .then()
fetchData()
    .then(data => console.log(data))
    .catch(error => console.error(error))
    .finally(() => console.log("完成"));

// async/await（ES2017+）
async function main() {
    try {
        const result = await fetchData();
        console.log(result);
        
        // 并发执行多个异步任务
        const results = await Promise.all([
            fetchData(),
            fetchData(),
            fetchData()
        ]);
        
        // 竞速（返回最快完成的）
        const fastest = await Promise.race([
            fetchData(),
            fetchData()
        ]);
        
    } catch (error) {
        console.error(error);
    }
}

main();

// 创建 Promise
const promise = new Promise((resolve, reject) => {
    if (success) {
        resolve(value);
    } else {
        reject(error);
    }
});

// Promise 链式调用
fetchData()
    .then(data => processData(data))
    .then(result => saveResult(result))
    .catch(error => handleError(error));
```

---

## 常用内置函数/方法

### Python 内置函数

**Python:**
```python
# 类型转换
int("42")           # 转换为整数
float("3.14")       # 转换为浮点数
str(42)             # 转换为字符串
bool(1)             # 转换为布尔值
list("abc")         # ['a', 'b', 'c'] - 转换为列表
tuple([1, 2, 3])    # (1, 2, 3) - 转换为元组
set([1, 2, 2, 3])   # {1, 2, 3} - 转换为集合
dict([("a", 1), ("b", 2)])  # {'a': 1, 'b': 2} - 转换为字典

# 数学函数
abs(-5)             # 5 - 绝对值
max(1, 2, 3)        # 3 - 最大值
min(1, 2, 3)        # 1 - 最小值
sum([1, 2, 3])      # 6 - 求和
pow(2, 3)           # 8 - 幂运算
round(3.14159, 2)   # 3.14 - 四舍五入
divmod(10, 3)       # (3, 1) - 返回商和余数

# 序列操作
len([1, 2, 3])      # 3 - 长度
sorted([3, 1, 2])   # [1, 2, 3] - 排序（返回新列表）
reversed([1, 2, 3]) # 反转迭代器
enumerate(['a', 'b', 'c'])  # [(0, 'a'), (1, 'b'), (2, 'c')] - 枚举
zip([1, 2], ['a', 'b'])     # [(1, 'a'), (2, 'b')] - 打包
all([True, True, False])    # False - 是否全为真
any([False, False, True])   # True - 是否有真值

# 函数式编程
map(lambda x: x**2, [1, 2, 3])      # [1, 4, 9] - 映射
filter(lambda x: x > 0, [-1, 0, 1]) # [1] - 过滤
reduce(lambda x, y: x + y, [1, 2, 3])  # 6 - 归约（需要 from functools import reduce）

# 对象操作
type(42)            # <class 'int'> - 获取类型
isinstance(42, int) # True - 检查类型
hasattr(obj, 'attr')  # 检查属性是否存在
getattr(obj, 'attr', default)  # 获取属性
setattr(obj, 'attr', value)    # 设置属性
delattr(obj, 'attr')           # 删除属性

# 输入输出
print("Hello")      # 打印输出
input("提示: ")     # 读取用户输入（返回字符串）

# 其他
range(5)            # range(0, 5) - 生成范围
range(1, 6)         # range(1, 6)
range(0, 10, 2)     # range(0, 10, 2) - 步长为2
id(obj)             # 获取对象的唯一标识符
dir(obj)            # 列出对象的所有属性和方法
help(obj)           # 查看对象的帮助文档
```

### JavaScript 常用方法

**JavaScript:**
```javascript
// 类型转换
Number("42")        // 转换为数字
String(42)          // 转换为字符串
Boolean(1)          // 转换为布尔值
Array.from("abc")   // ['a', 'b', 'c'] - 转换为数组

// 数学函数（Math 对象）
Math.abs(-5)        // 5 - 绝对值
Math.max(1, 2, 3)   // 3 - 最大值
Math.min(1, 2, 3)   // 1 - 最小值
Math.pow(2, 3)      // 8 - 幂运算
Math.sqrt(16)       // 4 - 平方根
Math.round(3.14)    // 3 - 四舍五入
Math.floor(3.9)     // 3 - 向下取整
Math.ceil(3.1)      // 4 - 向上取整
Math.random()       // 0-1 之间的随机数
Math.PI             // 3.141592653589793 - 圆周率

// 数组方法
[1, 2, 3].length    // 3 - 长度
[3, 1, 2].sort()    // [1, 2, 3] - 排序（原地修改）
[1, 2, 3].reverse() // [3, 2, 1] - 反转（原地修改）
[1, 2, 3].map(x => x**2)        // [1, 4, 9] - 映射
[1, 2, 3].filter(x => x > 1)    // [2, 3] - 过滤
[1, 2, 3].reduce((sum, x) => sum + x, 0)  // 6 - 归约
[1, 2, 3].forEach(x => console.log(x))    // 遍历
[1, 2, 3].every(x => x > 0)     // true - 是否全部满足
[1, 2, 3].some(x => x > 2)      // true - 是否有满足的
[1, 2, 3].find(x => x > 1)      // 2 - 查找第一个满足的
[1, 2, 3].findIndex(x => x > 1) // 1 - 查找索引
[1, 2, 3].includes(2)           // true - 是否包含
[1, 2, 3].join(", ")            // "1, 2, 3" - 连接为字符串

// 对象方法
Object.keys(obj)    // 获取所有键
Object.values(obj)  // 获取所有值
Object.entries(obj) // 获取所有键值对
Object.assign({}, obj1, obj2)  // 合并对象
Object.freeze(obj)  // 冻结对象（不可修改）
Object.seal(obj)    // 密封对象（不可添加/删除属性）

// 类型检查
typeof 42           // "number" - 获取类型
42 instanceof Number  // false - 检查实例
Array.isArray([])   // true - 检查是否为数组

// 输入输出
console.log("Hello")      // 打印输出
console.error("Error")    // 错误输出
console.warn("Warning")   // 警告输出
console.table(data)       // 表格输出
alert("消息")             // 浏览器弹窗
prompt("提示")            // 浏览器输入框

// JSON 操作
JSON.stringify(obj)       // 对象转 JSON 字符串
JSON.parse(jsonString)    // JSON 字符串转对象

// 定时器
setTimeout(() => {}, 1000)  // 延迟执行（毫秒）
setInterval(() => {}, 1000) // 定时重复执行
clearTimeout(timerId)       // 清除延迟
clearInterval(intervalId)   // 清除定时器
```

---

## Python 常用标准库 API

### os 模块 - 操作系统接口

```python
import os

# 文件和目录操作
os.getcwd()                 # 获取当前工作目录
os.chdir('/path/to/dir')    # 改变当前工作目录
os.listdir('.')             # 列出目录内容
os.mkdir('dirname')         # 创建目录
os.makedirs('dir/subdir')   # 递归创建目录
os.remove('file.txt')       # 删除文件
os.rmdir('dirname')         # 删除空目录
os.removedirs('dir/subdir') # 递归删除空目录
os.rename('old.txt', 'new.txt')  # 重命名文件/目录

# 路径操作
os.path.exists('file.txt')  # 检查路径是否存在
os.path.isfile('file.txt')  # 检查是否为文件
os.path.isdir('dirname')    # 检查是否为目录
os.path.join('dir', 'file.txt')  # 拼接路径
os.path.split('/path/to/file.txt')  # ('/path/to', 'file.txt') - 分割路径
os.path.dirname('/path/to/file.txt')  # '/path/to' - 获取目录名
os.path.basename('/path/to/file.txt')  # 'file.txt' - 获取文件名
os.path.abspath('file.txt')  # 获取绝对路径
os.path.getsize('file.txt')  # 获取文件大小（字节）

# 环境变量
os.environ['PATH']          # 获取环境变量
os.environ.get('PATH', '')  # 安全获取环境变量
os.getenv('PATH')           # 获取环境变量

# 执行系统命令
os.system('ls -l')          # 执行命令（返回退出码）
```

### sys 模块 - 系统相关

```python
import sys

sys.argv                    # 命令行参数列表
sys.exit(0)                 # 退出程序
sys.version                 # Python 版本信息
sys.platform                # 平台标识（'linux', 'win32', 'darwin'）
sys.path                    # 模块搜索路径列表
sys.stdin                   # 标准输入
sys.stdout                  # 标准输出
sys.stderr                  # 标准错误
```

### datetime 模块 - 日期时间

```python
from datetime import datetime, date, time, timedelta

# 获取当前时间
now = datetime.now()        # 当前日期时间
today = date.today()        # 当前日期
current_time = datetime.now().time()  # 当前时间

# 创建日期时间对象
dt = datetime(2024, 3, 15, 14, 30, 0)  # 2024-03-15 14:30:00
d = date(2024, 3, 15)       # 2024-03-15
t = time(14, 30, 0)         # 14:30:00

# 格式化
dt.strftime('%Y-%m-%d %H:%M:%S')  # '2024-03-15 14:30:00' - 格式化输出
datetime.strptime('2024-03-15', '%Y-%m-%d')  # 解析字符串

# 日期时间运算
delta = timedelta(days=7, hours=2, minutes=30)  # 时间差
future = now + delta        # 未来时间
past = now - delta          # 过去时间
diff = dt2 - dt1            # 计算时间差

# 获取属性
dt.year                     # 年
dt.month                    # 月
dt.day                      # 日
dt.hour                     # 时
dt.minute                   # 分
dt.second                   # 秒
dt.weekday()                # 星期几（0=周一）
```

### json 模块 - JSON 处理

```python
import json

# 序列化（Python 对象 -> JSON 字符串）
data = {'name': 'Alice', 'age': 25}
json_str = json.dumps(data)              # 转为 JSON 字符串
json_str = json.dumps(data, indent=2)    # 格式化输出
json_str = json.dumps(data, ensure_ascii=False)  # 支持中文

# 反序列化（JSON 字符串 -> Python 对象）
data = json.loads(json_str)

# 文件操作
with open('data.json', 'w') as f:
    json.dump(data, f, indent=2)        # 写入文件

with open('data.json', 'r') as f:
    data = json.load(f)                     # 从文件读取
```

### re 模块 - 正则表达式

```python
import re

# 匹配模式
pattern = r'\d+'            # 原始字符串，匹配数字

# 查找
re.search(pattern, text)    # 查找第一个匹配（返回 Match 对象）
re.match(pattern, text)     # 从开头匹配
re.findall(pattern, text)   # 查找所有匹配（返回列表）
re.finditer(pattern, text)  # 查找所有匹配（返回迭代器）

# 替换
re.sub(pattern, replacement, text)  # 替换所有匹配
re.subn(pattern, replacement, text) # 替换并返回替换次数

# 分割
re.split(pattern, text)     # 按模式分割字符串

# 编译正则表达式（提高性能）
compiled = re.compile(pattern)
compiled.search(text)

# Match 对象方法
match = re.search(r'(\d+)', text)
match.group()               # 获取匹配的字符串
match.group(1)              # 获取第一个捕获组
match.start()               # 匹配开始位置
match.end()                 # 匹配结束位置
match.span()                # (start, end) 元组

# 常用正则模式
r'\d'       # 数字
r'\w'       # 字母、数字、下划线
r'\s'       # 空白字符
r'.'        # 任意字符（除换行符）
r'^'        # 字符串开头
r'$'        # 字符串结尾
r'*'        # 0次或多次
r'+'        # 1次或多次
r'?'        # 0次或1次
r'{n}'      # 恰好n次
r'{n,m}'    # n到m次
```

### pathlib 模块 - 面向对象的路径操作

```python
from pathlib import Path

# 创建路径对象
p = Path('.')               # 当前目录
p = Path('/path/to/file.txt')
p = Path.home()             # 用户主目录
p = Path.cwd()              # 当前工作目录

# 路径操作
p.exists()                  # 检查是否存在
p.is_file()                 # 是否为文件
p.is_dir()                  # 是否为目录
p.name                      # 'file.txt' - 文件名
p.stem                      # 'file' - 文件名（不含扩展名）
p.suffix                    # '.txt' - 扩展名
p.parent                    # 父目录
p.absolute()                # 绝对路径

# 路径拼接
p = Path('dir') / 'subdir' / 'file.txt'

# 文件操作
p.read_text()               # 读取文本文件
p.write_text('content')     # 写入文本文件
p.read_bytes()              # 读取二进制文件
p.write_bytes(b'content')   # 写入二进制文件

# 目录操作
p.mkdir()                   # 创建目录
p.mkdir(parents=True, exist_ok=True)  # 递归创建
p.rmdir()                   # 删除空目录
p.unlink()                  # 删除文件
p.rename('new_name.txt')    # 重命名

# 遍历目录
p.iterdir()                 # 遍历目录内容
p.glob('*.txt')             # 匹配文件模式
p.rglob('*.txt')            # 递归匹配
```

### collections 模块 - 容器数据类型

```python
from collections import Counter, defaultdict, deque, namedtuple, OrderedDict

# Counter - 计数器
counter = Counter([1, 2, 2, 3, 3, 3])
counter[2]                  # 2 - 获取计数
counter.most_common(2)      # [(3, 3), (2, 2)] - 最常见的元素
counter.update([1, 2])      # 更新计数

# defaultdict - 带默认值的字典
dd = defaultdict(int)       # 默认值为 0
dd['key'] += 1              # 不存在时自动创建
dd = defaultdict(list)      # 默认值为空列表
dd['key'].append(1)

# deque - 双端队列
dq = deque([1, 2, 3])
dq.append(4)                # 右端添加
dq.appendleft(0)            # 左端添加
dq.pop()                    # 右端删除
dq.popleft()                # 左端删除
dq.rotate(1)                # 旋转

# namedtuple - 命名元组
Point = namedtuple('Point', ['x', 'y'])
p = Point(1, 2)
p.x                         # 1 - 通过名称访问
p[0]                        # 1 - 通过索引访问

# OrderedDict - 有序字典（Python 3.7+ 普通字典已有序）
od = OrderedDict()
od['a'] = 1
od['b'] = 2
```

### itertools 模块 - 迭代器工具

```python
from itertools import count, cycle, repeat, chain, combinations, permutations

# 无限迭代器
count(10)                   # 10, 11, 12, ... - 无限计数
cycle([1, 2, 3])            # 1, 2, 3, 1, 2, 3, ... - 循环
repeat(10, 3)               # 10, 10, 10 - 重复

# 组合迭代器
chain([1, 2], [3, 4])    # 1, 2, 3, 4 - 连接多个迭代器
combinations([1, 2, 3], 2)  # (1,2), (1,3), (2,3) - 组合
permutations([1, 2, 3], 2)  # (1,2), (1,3), (2,1), (2,3), (3,1), (3,2) - 排列
```

### random 模块 - 随机数生成

```python
import random

# 随机数
random.random()             # 0-1 之间的随机浮点数
random.uniform(1, 10)       # 1-10 之间的随机浮点数
random.randint(1, 10)       # 1-10 之间的随机整数（包含两端）
random.randrange(0, 10, 2)  # 0-10 之间的随机偶数

# 序列操作
random.choice([1, 2, 3])    # 随机选择一个元素
random.choices([1, 2, 3], k=2)  # 随机选择多个元素（可重复）
random.sample([1, 2, 3], 2) # 随机选择多个元素（不重复）
random.shuffle(lst)         # 原地打乱列表

# 设置随机种子（用于可重复的随机结果）
random.seed(42)
```

### math 模块 - 数学函数

```python
import math

# 基本数学函数
math.ceil(3.2)              # 4 - 向上取整
math.floor(3.8)             # 3 - 向下取整
math.trunc(3.8)             # 3 - 截断小数部分
math.sqrt(16)               # 4.0 - 平方根
math.pow(2, 3)              # 8.0 - 幂运算
math.exp(1)                 # e^1 - 指数函数
math.log(10)                # ln(10) - 自然对数
math.log10(100)             # 2.0 - 以10为底的对数
math.log2(8)                # 3.0 - 以2为底的对数

# 三角函数
math.sin(math.pi / 2)       # 1.0 - 正弦
math.cos(0)                 # 1.0 - 余弦
math.tan(math.pi / 4)       # 1.0 - 正切
math.asin(1)                # π/2 - 反正弦
math.acos(1)                # 0 - 反余弦
math.atan(1)                # π/4 - 反正切

# 常数
math.pi                     # 3.141592653589793 - 圆周率
math.e                      # 2.718281828459045 - 自然常数
math.inf                    # 无穷大
math.nan                    # 非数字

# 其他
math.factorial(5)           # 120 - 阶乘
math.gcd(12, 18)            # 6 - 最大公约数
math.isnan(value)           # 检查是否为 NaN
math.isinf(value)           # 检查是否为无穷大
```

### time 模块 - 时间相关

```python
import time

# 时间戳
time.time()                 # 当前时间戳（秒）

# 休眠
time.sleep(1)               # 休眠1秒

# 时间格式化
time.strftime('%Y-%m-%d %H:%M:%S')  # 格式化当前时间
time.strptime('2024-03-15', '%Y-%m-%d')  # 解析时间字符串

# 性能计时
start = time.perf_counter()
# ... 代码 ...
elapsed = time.perf_counter() - start
```

### subprocess 模块 - 子进程管理

```python
import subprocess

# 执行命令
result = subprocess.run(['ls', '-l'], capture_output=True, text=True)
result.returncode          # 返回码
result.stdout              # 标准输出
result.stderr              # 标准错误

# 简单执行
subprocess.run(['python', 'script.py'])

# 获取输出
output = subprocess.check_output(['echo', 'hello'], text=True)

# 管道
p1 = subprocess.Popen(['ls'], stdout=subprocess.PIPE)
p2 = subprocess.Popen(['grep', 'txt'], stdin=p1.stdout, stdout=subprocess.PIPE)
output = p2.communicate()[0]
```

### urllib 模块 - URL 处理

```python
from urllib import request, parse

# HTTP 请求
response = request.urlopen('https://api.example.com')
html = response.read().decode('utf-8')
response.status            # HTTP 状态码

# URL 编码/解码
encoded = parse.quote('中文')           # URL 编码
decoded = parse.unquote(encoded)       # URL 解码

# 解析 URL
parsed = parse.urlparse('https://example.com/path?key=value')
parsed.scheme              # 'https'
parsed.netloc              # 'example.com'
parsed.path                # '/path'
parsed.query               # 'key=value'
```

### csv 模块 - CSV 文件处理

```python
import csv

# 读取 CSV
with open('data.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)          # 每行是一个列表

# 读取为字典
with open('data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row['column_name'])  # 每行是一个字典

# 写入 CSV
with open('data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Age'])
    writer.writerow(['Alice', 25])
    writer.writerows([['Bob', 30], ['Charlie', 35]])

# 写入字典
with open('data.csv', 'w', newline='') as f:
    fieldnames = ['Name', 'Age']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({'Name': 'Alice', 'Age': 25})
```

### pickle 模块 - 对象序列化

```python
import pickle

# 序列化（保存对象）
data = {'name': 'Alice', 'age': 25}
with open('data.pkl', 'wb') as f:
    pickle.dump(data, f)

# 反序列化（加载对象）
with open('data.pkl', 'rb') as f:
    data = pickle.load(f)

# 序列化为字节串
bytes_data = pickle.dumps(data)
data = pickle.loads(bytes_data)
```

### logging 模块 - 日志记录

```python
import logging

# 基本配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)

# 记录日志
logging.debug('调试信息')
logging.info('普通信息')
logging.warning('警告信息')
logging.error('错误信息')
logging.critical('严重错误')

# 创建 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 添加处理器
handler = logging.FileHandler('app.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 使用 logger
logger.info('这是一条日志')
```

### argparse 模块 - 命令行参数解析

```python
import argparse

# 创建解析器
parser = argparse.ArgumentParser(description='程序描述')

# 添加参数
parser.add_argument('input', help='输入文件')  # 位置参数
parser.add_argument('-o', '--output', help='输出文件')  # 可选参数
parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
parser.add_argument('-n', '--number', type=int, default=10, help='数量')

# 解析参数
args = parser.parse_args()

# 使用参数
print(args.input)
print(args.output)
if args.verbose:
    print('详细模式')
```

### threading 模块 - 多线程

```python
import threading

# 创建线程
def worker(name):
    print(f'线程 {name} 开始')
    time.sleep(1)
    print(f'线程 {name} 结束')

thread = threading.Thread(target=worker, args=('A',))
thread.start()
thread.join()               # 等待线程结束

# 线程锁
lock = threading.Lock()
with lock:
    # 临界区代码
    pass

# 线程池
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(worker, i) for i in range(10)]
    for future in futures:
        result = future.result()
```

### multiprocessing 模块 - 多进程

```python
from multiprocessing import Process, Pool, Queue

# 创建进程
def worker(name):
    print(f'进程 {name} 开始')

process = Process(target=worker, args=('A',))
process.start()
process.join()

# 进程池
with Pool(processes=4) as pool:
    results = pool.map(func, [1, 2, 3, 4])

# 进程间通信
queue = Queue()
queue.put('消息')
message = queue.get()
```

### requests 模块 - HTTP 请求（第三方库）

```python
import requests

# GET 请求
response = requests.get('https://api.example.com')
response.status_code       # 状态码
response.text              # 响应文本
response.json()            # 解析 JSON
response.headers           # 响应头

# POST 请求
data = {'key': 'value'}
response = requests.post('https://api.example.com', json=data)

# 带参数的请求
params = {'page': 1, 'limit': 10}
response = requests.get('https://api.example.com', params=params)

# 带请求头
headers = {'Authorization': 'Bearer token'}
response = requests.get('https://api.example.com', headers=headers)

# 超时设置
response = requests.get('https://api.example.com', timeout=5)

# 会话（保持 Cookie）
session = requests.Session()
session.get('https://api.example.com')
```

---

## 总结

这份对比手册涵盖了 Python 和 JavaScript 的主要语法差异，以及 Python 常用标准库的 API。主要区别：

1. Python 使用缩进定义代码块，JavaScript 使用花括号
2. Python 变量无需声明类型，JavaScript 使用 let/const/var
3. Python 使用 `def` 定义函数，JavaScript 使用 `function` 或箭头函数
4. Python 使用 `self` 表示实例，JavaScript 使用 `this`
5. Python 使用 `import`，JavaScript 使用 `import/require`
6. Python 异步使用 `async/await` + `asyncio`，JavaScript 使用 `async/await` + `Promise`

掌握这些差异和常用 API，可以帮助你在两种语言之间快速切换和开发。
