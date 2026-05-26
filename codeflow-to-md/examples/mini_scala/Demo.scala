object Demo {
  def main(args: Array[String]): Unit = {
    val svc = new Service()
    svc.run()
  }
}

class Service {
  def run(): Unit = {
    helper()
  }

  def helper(): Unit = {}
}
