import com.sun.source.tree.AssignmentTree;
import com.sun.source.tree.BinaryTree;
import com.sun.source.tree.ClassTree;
import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.tree.ExpressionTree;
import com.sun.source.tree.IdentifierTree;
import com.sun.source.tree.LiteralTree;
import com.sun.source.tree.MemberSelectTree;
import com.sun.source.tree.MethodInvocationTree;
import com.sun.source.tree.MethodTree;
import com.sun.source.tree.ParenthesizedTree;
import com.sun.source.tree.ReturnTree;
import com.sun.source.tree.Tree;
import com.sun.source.tree.TypeCastTree;
import com.sun.source.tree.VariableTree;
import com.sun.source.util.JavacTask;
import com.sun.source.util.SourcePositions;
import com.sun.source.util.TreePath;
import com.sun.source.util.TreePathScanner;
import com.sun.source.util.Trees;

import javax.lang.model.element.Element;
import javax.lang.model.element.ElementKind;
import javax.lang.model.element.ExecutableElement;
import javax.lang.model.element.TypeElement;
import javax.lang.model.element.VariableElement;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Deque;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;

/**
 * Compiler-backed Java AST extractor for the softKeyData vertical slice.
 *
 * It emits JSONL records. Parsing remains useful even when semantic analysis fails;
 * unresolved elements are emitted explicitly rather than being treated as absence.
 */
public final class CodeGraphAstExtractor {
    private CodeGraphAstExtractor() {}

    public static void main(String[] args) throws Exception {
        Args parsed = Args.parse(args);
        if (parsed.files.isEmpty()) {
            System.err.println("usage: CodeGraphAstExtractor --root <root> [--classpath <cp>] -- <files...>");
            System.exit(2);
        }
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            throw new IllegalStateException("JDK compiler not available; run with a JDK, not a JRE");
        }
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager fileManager = compiler.getStandardFileManager(diagnostics, Locale.ROOT, null)) {
            Iterable<? extends JavaFileObject> units = fileManager.getJavaFileObjectsFromFiles(
                    parsed.files.stream().map(File::new).toList());
            List<String> options = new ArrayList<>(List.of("-proc:none", "-Xlint:none"));
            if (!parsed.classpath.isBlank()) {
                options.addAll(List.of("-classpath", parsed.classpath));
            }
            JavacTask task = (JavacTask) compiler.getTask(null, fileManager, diagnostics, options, null, units);
            List<CompilationUnitTree> trees = new ArrayList<>();
            for (CompilationUnitTree unit : task.parse()) {
                trees.add(unit);
            }
            boolean semanticReady = true;
            try {
                task.analyze();
            } catch (Throwable failure) {
                semanticReady = false;
                emit(Map.of(
                        "record", "diagnostic",
                        "code", "JAVA_SEMANTIC_ANALYSIS_FAILED",
                        "severity", "warning",
                        "summary", failure.getClass().getSimpleName() + ": " + Objects.toString(failure.getMessage(), "")
                ));
            }
            Trees treeApi = Trees.instance(task);
            Extractor extractor = new Extractor(parsed.root, treeApi, semanticReady);
            for (CompilationUnitTree unit : trees) {
                extractor.scan(unit, null);
            }
            for (Diagnostic<? extends JavaFileObject> diagnostic : diagnostics.getDiagnostics()) {
                String source = diagnostic.getSource() == null ? "" : diagnostic.getSource().getName();
                emit(Map.of(
                        "record", "diagnostic",
                        "code", "JAVAC_" + diagnostic.getKind().name(),
                        "severity", diagnostic.getKind() == Diagnostic.Kind.ERROR ? "warning" : "info",
                        "summary", diagnostic.getMessage(Locale.ROOT),
                        "source", source,
                        "line", diagnostic.getLineNumber()
                ));
            }
        }
    }

    private static final class Args {
        final Path root;
        final String classpath;
        final List<String> files;

        private Args(Path root, String classpath, List<String> files) {
            this.root = root;
            this.classpath = classpath;
            this.files = files;
        }

        static Args parse(String[] args) {
            Path root = Paths.get(".").toAbsolutePath().normalize();
            String classpath = "";
            List<String> files = new ArrayList<>();
            boolean positional = false;
            for (int index = 0; index < args.length; index++) {
                String arg = args[index];
                if ("--".equals(arg)) {
                    positional = true;
                } else if (!positional && "--root".equals(arg) && index + 1 < args.length) {
                    root = Paths.get(args[++index]).toAbsolutePath().normalize();
                } else if (!positional && "--classpath".equals(arg) && index + 1 < args.length) {
                    classpath = args[++index];
                } else {
                    files.add(arg);
                }
            }
            return new Args(root, classpath, files);
        }
    }

    private static final class Extractor extends TreePathScanner<Void, Void> {
        private final Path root;
        private final Trees trees;
        private final SourcePositions positions;
        private final boolean semanticReady;
        private final Deque<String> methodStack = new ArrayDeque<>();
        private final Map<String, Boolean> emittedNodes = new HashMap<>();
        private CompilationUnitTree unit;
        private String relativePath = "";

        Extractor(Path root, Trees trees, boolean semanticReady) {
            this.root = root;
            this.trees = trees;
            this.positions = trees.getSourcePositions();
            this.semanticReady = semanticReady;
        }

        @Override
        public Void visitCompilationUnit(CompilationUnitTree tree, Void unused) {
            CompilationUnitTree previous = unit;
            String previousPath = relativePath;
            unit = tree;
            try {
                Path absolute = Paths.get(tree.getSourceFile().toUri()).toAbsolutePath().normalize();
                relativePath = root.relativize(absolute).toString().replace(File.separatorChar, '/');
            } catch (Exception ignored) {
                relativePath = tree.getSourceFile().getName().replace(File.separatorChar, '/');
            }
            try {
                return super.visitCompilationUnit(tree, unused);
            } finally {
                unit = previous;
                relativePath = previousPath;
            }
        }

        @Override
        public Void visitClass(ClassTree tree, Void unused) {
            Element element = safeElement(getCurrentPath());
            String id = elementId(element, "class", tree.getSimpleName().toString());
            emitNode(id, "class", tree.getSimpleName().toString(), tree, element, Map.of());
            return super.visitClass(tree, unused);
        }

        @Override
        public Void visitMethod(MethodTree tree, Void unused) {
            Element element = safeElement(getCurrentPath());
            String fallback = tree.getName() + "(" + tree.getParameters().size() + ")";
            String id = elementId(element, "method", fallback);
            emitNode(id, "method", tree.getName().toString(), tree, element, Map.of(
                    "semantic_resolved", element instanceof ExecutableElement,
                    "qualified_name", qualifiedName(element, fallback)
            ));
            methodStack.push(id);
            try {
                return super.visitMethod(tree, unused);
            } finally {
                methodStack.pop();
            }
        }

        @Override
        public Void visitVariable(VariableTree tree, Void unused) {
            Element element = safeElement(getCurrentPath());
            boolean syntacticParameter = getCurrentPath().getParentPath() != null
                    && getCurrentPath().getParentPath().getLeaf() instanceof MethodTree parentMethod
                    && parentMethod.getParameters().contains(tree);
            boolean isParameter = (element != null && element.getKind() == ElementKind.PARAMETER) || syntacticParameter;
            String id = elementId(element, isParameter ? "parameter" : "variable", tree.getName().toString());
            String kind = isParameter ? "parameter" : "variable";
            emitNode(id, kind, tree.getName().toString(), tree, element, Map.of(
                    "qualified_name", qualifiedName(element, tree.getName().toString())
            ));
            if (tree.getInitializer() != null) {
                String source = expressionNode(tree.getInitializer());
                if (source != null) {
                    emitEdge(source, id, "DATA_FLOW", tree, Map.of("operation", "initializer"));
                }
            }
            return super.visitVariable(tree, unused);
        }

        @Override
        public Void visitAssignment(AssignmentTree tree, Void unused) {
            String source = expressionNode(tree.getExpression());
            String target = expressionNode(tree.getVariable());
            if (source != null && target != null) {
                emitEdge(source, target, "DATA_FLOW", tree, Map.of("operation", "assignment"));
            }
            return super.visitAssignment(tree, unused);
        }

        @Override
        public Void visitReturn(ReturnTree tree, Void unused) {
            if (!methodStack.isEmpty() && tree.getExpression() != null) {
                String source = expressionNode(tree.getExpression());
                String returnNode = methodStack.peek() + ":return";
                emitSyntheticNode(returnNode, "return", "return", tree, Map.of());
                if (source != null) {
                    emitEdge(source, returnNode, "DATA_FLOW", tree, Map.of("operation", "return"));
                }
            }
            return super.visitReturn(tree, unused);
        }

        @Override
        public Void visitMethodInvocation(MethodInvocationTree tree, Void unused) {
            Element element = safeElement(getCurrentPath());
            String methodName = invocationName(tree);
            String target = elementId(element, "method", methodName + "(?)");
            emitNode(target, "method", methodName, tree, element, Map.of(
                    "semantic_resolved", element instanceof ExecutableElement,
                    "qualified_name", qualifiedName(element, methodName)
            ));
            if (!methodStack.isEmpty()) {
                emitEdge(methodStack.peek(), target, "CALL", tree, Map.of(
                        "semantic_resolved", element instanceof ExecutableElement
                ));
            }
            if (element instanceof ExecutableElement executable) {
                List<? extends VariableElement> parameters = executable.getParameters();
                for (int index = 0; index < Math.min(parameters.size(), tree.getArguments().size()); index++) {
                    String source = expressionNode(tree.getArguments().get(index));
                    VariableElement parameter = parameters.get(index);
                    String parameterId = elementId(parameter, "parameter", parameter.getSimpleName().toString());
                    emitNode(parameterId, "parameter", parameter.getSimpleName().toString(), tree, parameter, Map.of(
                            "argument_index", index,
                            "qualified_name", qualifiedName(parameter, parameter.getSimpleName().toString())
                    ));
                    if (source != null) {
                        emitEdge(source, parameterId, "ARGUMENT_TO_PARAMETER", tree, Map.of("argument_index", index));
                    }
                }
            } else if (!tree.getArguments().isEmpty()) {
                for (int index = 0; index < tree.getArguments().size(); index++) {
                    String source = expressionNode(tree.getArguments().get(index));
                    String parameterId = target + ":arg" + index;
                    emitSyntheticNode(parameterId, "parameter", "arg" + index, tree, Map.of("semantic_resolved", false));
                    if (source != null) {
                        emitEdge(source, parameterId, "ARGUMENT_TO_PARAMETER", tree, Map.of(
                                "argument_index", index,
                                "semantic_resolved", false
                        ));
                    }
                }
            }

            if (("put".equals(methodName) || "set".equals(methodName) || "addProperty".equals(methodName)
                    || "add".equals(methodName) || "append".equals(methodName)) && tree.getArguments().size() >= 2) {
                String key = literalString(tree.getArguments().get(0));
                if (key != null) {
                    String payloadId = "payload-field:" + key;
                    emitSyntheticNode(payloadId, "payload_field", key, tree, Map.of("payload_key", key));
                    String source = expressionNode(tree.getArguments().get(1));
                    if (source != null) {
                        emitEdge(source, payloadId, "HTTP_PAYLOAD", tree, Map.of("payload_key", key));
                    }
                }
            }
            if (("post".equals(methodName) || "request".equals(methodName)) && !tree.getArguments().isEmpty()) {
                String route = literalString(tree.getArguments().get(0));
                if (route != null) {
                    String endpointId = "endpoint:" + route;
                    emitSyntheticNode(endpointId, "endpoint", route, tree, Map.of("route", route));
                    if (!methodStack.isEmpty()) {
                        emitEdge(methodStack.peek(), endpointId, "HTTP_REQUEST", tree, Map.of("route", route));
                    }
                    if (tree.getArguments().size() >= 2) {
                        String payload = expressionNode(tree.getArguments().get(1));
                        if (payload != null) {
                            emitEdge(payload, endpointId, "ROUTES_TO", tree, Map.of("route", route));
                        }
                    }
                }
            }
            return super.visitMethodInvocation(tree, unused);
        }

        private String expressionNode(ExpressionTree tree) {
            if (tree == null) {
                return null;
            }
            if (tree instanceof ParenthesizedTree parenthesized) {
                return expressionNode(parenthesized.getExpression());
            }
            if (tree instanceof TypeCastTree cast) {
                return expressionNode(cast.getExpression());
            }
            if (tree instanceof IdentifierTree || tree instanceof MemberSelectTree) {
                TreePath path = new TreePath(getCurrentPath(), tree);
                Element element = safeElement(path);
                String fallback = tree.toString();
                String id = elementId(element, "value", fallback);
                String kind = element == null ? "value" : switch (element.getKind()) {
                    case FIELD -> "field";
                    case PARAMETER -> "parameter";
                    case LOCAL_VARIABLE, RESOURCE_VARIABLE -> "variable";
                    case METHOD, CONSTRUCTOR -> "method";
                    default -> "value";
                };
                emitNode(id, kind, element == null ? fallback : element.getSimpleName().toString(), tree, element, Map.of(
                        "semantic_resolved", element != null,
                        "qualified_name", qualifiedName(element, fallback)
                ));
                return id;
            }
            if (tree instanceof MethodInvocationTree invocation) {
                TreePath path = new TreePath(getCurrentPath(), tree);
                Element element = safeElement(path);
                String target = elementId(element, "method", invocationName(invocation) + "(?)");
                emitNode(target, "method", invocationName(invocation), tree, element, Map.of(
                        "semantic_resolved", element instanceof ExecutableElement,
                        "qualified_name", qualifiedName(element, invocationName(invocation))
                ));
                String returnId = target + ":return";
                emitSyntheticNode(returnId, "return", invocationName(invocation) + " return", tree, Map.of());
                return returnId;
            }
            if (tree instanceof LiteralTree literal) {
                String value = Objects.toString(literal.getValue(), "null");
                String id = "literal:" + Integer.toHexString(value.hashCode()) + ":" + sanitize(value);
                emitSyntheticNode(id, "literal", value, tree, Map.of("value", value));
                return id;
            }
            if (tree instanceof BinaryTree binary) {
                String id = "expression:" + relativePath + ":" + startLine(tree) + ":" + sanitize(tree.toString());
                emitSyntheticNode(id, "expression", tree.getKind().name(), tree, Map.of("expression", tree.toString()));
                String left = expressionNode(binary.getLeftOperand());
                String right = expressionNode(binary.getRightOperand());
                if (left != null) emitEdge(left, id, "DATA_FLOW", tree, Map.of("operand", "left"));
                if (right != null) emitEdge(right, id, "DATA_FLOW", tree, Map.of("operand", "right"));
                return id;
            }
            String id = "expression:" + relativePath + ":" + startLine(tree) + ":" + sanitize(tree.toString());
            emitSyntheticNode(id, "expression", tree.getKind().name(), tree, Map.of("expression", tree.toString()));
            return id;
        }

        private Element safeElement(TreePath path) {
            if (!semanticReady || path == null) return null;
            try {
                return trees.getElement(path);
            } catch (Throwable ignored) {
                return null;
            }
        }

        private String elementId(Element element, String fallbackKind, String fallback) {
            if (element == null) {
                return "java-unresolved:" + relativePath + ":" + fallbackKind + ":" + sanitize(fallback);
            }
            return "java:" + sanitize(qualifiedName(element, fallback));
        }

        private String qualifiedName(Element element, String fallback) {
            if (element == null) return fallback;
            if (element instanceof TypeElement type) {
                return type.getQualifiedName().toString();
            }
            if (element instanceof ExecutableElement executable) {
                String owner = qualifiedName(executable.getEnclosingElement(), "");
                String parameters = executable.getParameters().stream()
                        .map(parameter -> parameter.asType().toString())
                        .reduce((left, right) -> left + "," + right)
                        .orElse("");
                return owner + "." + executable.getSimpleName() + "(" + parameters + ")";
            }
            String owner = element.getEnclosingElement() == null ? "" : qualifiedName(element.getEnclosingElement(), "");
            return owner + "." + element.getSimpleName();
        }

        private void emitNode(String id, String kind, String label, Tree tree, Element element, Map<String, Object> metadata) {
            if (emittedNodes.putIfAbsent(id, Boolean.TRUE) != null) return;
            Map<String, Object> record = new LinkedHashMap<>();
            record.put("record", "node");
            record.put("id", id);
            record.put("kind", kind);
            record.put("label", label);
            record.put("path", relativePath);
            record.put("start_line", startLine(tree));
            record.put("end_line", endLine(tree));
            record.put("symbol", qualifiedName(element, label));
            record.put("metadata", metadata);
            emit(record);
        }

        private void emitSyntheticNode(String id, String kind, String label, Tree tree, Map<String, Object> metadata) {
            emitNode(id, kind, label, tree, null, metadata);
        }

        private void emitEdge(String source, String target, String kind, Tree tree, Map<String, Object> metadata) {
            Map<String, Object> record = new LinkedHashMap<>();
            record.put("record", "edge");
            record.put("source", source);
            record.put("target", target);
            record.put("kind", kind);
            record.put("path", relativePath);
            record.put("line", startLine(tree));
            record.put("metadata", metadata);
            emit(record);
        }

        private long startLine(Tree tree) {
            if (unit == null || tree == null || unit.getLineMap() == null) return 1;
            long position = positions.getStartPosition(unit, tree);
            return position < 0 ? 1 : unit.getLineMap().getLineNumber(position);
        }

        private long endLine(Tree tree) {
            if (unit == null || tree == null || unit.getLineMap() == null) return startLine(tree);
            long position = positions.getEndPosition(unit, tree);
            return position < 0 ? startLine(tree) : unit.getLineMap().getLineNumber(position);
        }
    }

    private static String invocationName(MethodInvocationTree tree) {
        ExpressionTree select = tree.getMethodSelect();
        if (select instanceof IdentifierTree identifier) {
            return identifier.getName().toString();
        }
        if (select instanceof MemberSelectTree member) {
            return member.getIdentifier().toString();
        }
        return select.toString();
    }

    private static String literalString(ExpressionTree tree) {
        if (tree instanceof LiteralTree literal && literal.getValue() instanceof String value) {
            return value;
        }
        return null;
    }

    private static String sanitize(String value) {
        String clean = value.replaceAll("[^A-Za-z0-9_.$:/()<>,-]+", "_");
        return clean.length() > 120 ? clean.substring(0, 120) : clean;
    }

    private static void emit(Map<String, ?> record) {
        System.out.println(toJson(record));
    }

    private static String toJson(Object value) {
        if (value == null) return "null";
        if (value instanceof String text) return "\"" + escape(text) + "\"";
        if (value instanceof Number || value instanceof Boolean) return value.toString();
        if (value instanceof Map<?, ?> map) {
            StringBuilder builder = new StringBuilder("{");
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) builder.append(',');
                first = false;
                builder.append(toJson(Objects.toString(entry.getKey()))).append(':').append(toJson(entry.getValue()));
            }
            return builder.append('}').toString();
        }
        if (value instanceof Iterable<?> iterable) {
            StringBuilder builder = new StringBuilder("[");
            boolean first = true;
            for (Object item : iterable) {
                if (!first) builder.append(',');
                first = false;
                builder.append(toJson(item));
            }
            return builder.append(']').toString();
        }
        if (value.getClass().isArray()) {
            return toJson(Arrays.asList((Object[]) value));
        }
        return toJson(value.toString());
    }

    private static String escape(String value) {
        StringBuilder builder = new StringBuilder();
        for (int index = 0; index < value.length(); index++) {
            char ch = value.charAt(index);
            switch (ch) {
                case '\\' -> builder.append("\\\\");
                case '"' -> builder.append("\\\"");
                case '\n' -> builder.append("\\n");
                case '\r' -> builder.append("\\r");
                case '\t' -> builder.append("\\t");
                default -> {
                    if (ch < 0x20) builder.append(String.format("\\u%04x", (int) ch));
                    else builder.append(ch);
                }
            }
        }
        return builder.toString();
    }
}
