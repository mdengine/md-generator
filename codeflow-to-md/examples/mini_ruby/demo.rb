# Sample flow: ClassA#a → b → ClassB#method1

class ClassB
  def method1
  end

  def method2
  end
end

class ClassA
  def a
    b
  end

  def b
    ClassB.new.method1
  end
end

def main
  ClassA.new.a
end
