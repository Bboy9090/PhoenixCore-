import {
  createOperationPreview,
  getOperationCatalog,
  rejectOperationCommit
} from "../mock/mock-operations";
import type { OperationPreviewRequest } from "../types/operation";

export function listOperationCatalog() {
  const operations = getOperationCatalog();

  return {
    operations,
    count: operations.length,
    source: "safe-static-catalog"
  };
}

export function previewOperation(body: OperationPreviewRequest) {
  return createOperationPreview(body);
}

export function commitOperation(body: unknown) {
  return rejectOperationCommit(body);
}
