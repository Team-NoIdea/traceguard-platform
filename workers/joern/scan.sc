import io.shiftleft.semanticcpg.language.*
import io.joern.dataflowengineoss.language.*
import java.nio.file.{Files, Paths}

@main def exec(): Unit = {
  importCode.python("/workspace/src")
  run.ossdataflow
  val queries = List(
    ("python-eval-flow", "CWE-95", "eval", "Untrusted input reaches eval"),
    ("python-command-flow", "CWE-78", "(system|popen)", "Untrusted input reaches a shell"),
    ("python-sql-flow", "CWE-89", "(execute|executemany)", "Untrusted input reaches SQL execution")
  )
  val findings = queries.flatMap { case (rule, cwe, sinkName, message) =>
    def sources = cpg.call.name("(input|get|json)").l ++ cpg.method.parameter.filterNot(_.name == "self").l
    cpg.call.name(sinkName).l.flatMap { sink =>
      val paths = sink.argument.reachableByFlows(sources.iterator).l
      paths.map { path =>
        ujson.Obj("rule" -> rule, "cwe" -> cwe, "message" -> message,
          "file" -> sink.file.name.headOption.getOrElse("unknown"),
          "line" -> sink.lineNumber.getOrElse(0),
          "flow" -> ujson.Arr.from(path.elements.map(_.code)))
      }
    }
  }
  Files.writeString(Paths.get("/workspace/out/results.json"), ujson.write(ujson.Obj("findings" -> ujson.Arr.from(findings))))
}
