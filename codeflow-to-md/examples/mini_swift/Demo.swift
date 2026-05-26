/// Sample flow: ClassA.a → b → ClassB.method1 / method2

struct ClassB {
    func method1() {}
    func method2() {}
}

struct ClassA {
    func a() {
        b()
    }

    func b() {
        ClassB().method1()
    }
}

func main() {
    ClassA().a()
}
