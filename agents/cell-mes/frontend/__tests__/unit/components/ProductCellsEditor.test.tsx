import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ProductCellsEditor from "@/components/master/ProductCellsEditor";
import { cellService } from "@/services/cell";
import { productService } from "@/services/master";

vi.mock("@/services/cell", () => ({ cellService: { getAll: vi.fn() } }));
vi.mock("@/services/master", () => ({ productService: { getCells: vi.fn(), saveCells: vi.fn() } }));

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const onDirtyChange = vi.fn();
  render(<QueryClientProvider client={client}>
    <ProductCellsEditor productId={1} onDirtyChange={onDirtyChange} onBusyChange={vi.fn()} />
  </QueryClientProvider>);
  return { client, onDirtyChange };
}

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(cellService.getAll).mockResolvedValue([
    { id: 1, code: "CELL-A", name: "Cell A", location: null, created_at: "2026-09-29" },
    { id: 2, code: "CELL-B", name: "Cell B", location: null, created_at: "2026-09-29" },
  ]);
  vi.mocked(productService.getCells).mockResolvedValue({ product_id: 1, cell_ids: [] });
  vi.mocked(productService.saveCells).mockImplementation(async (id, cell_ids) => ({ product_id: id, cell_ids }));
});

describe("ProductCellsEditor", () => {
  it("saves multiple allowed cells and clears them explicitly", async () => {
    const { onDirtyChange } = setup();
    await screen.findByText("허용 Cell 미지정");
    const a = screen.getByRole("checkbox", { name: "Cell A (CELL-A)" });
    const b = screen.getByRole("checkbox", { name: "Cell B (CELL-B)" });
    fireEvent.click(a);
    fireEvent.click(b);
    expect(onDirtyChange).toHaveBeenLastCalledWith(true);
    fireEvent.click(screen.getByRole("button", { name: "Cell 저장" }));
    await screen.findByText("Cell 저장 완료");
    expect(productService.saveCells).toHaveBeenLastCalledWith(1, [1, 2]);
    expect(onDirtyChange).toHaveBeenLastCalledWith(false);
    fireEvent.click(a);
    fireEvent.click(b);
    fireEvent.click(screen.getByRole("button", { name: "Cell 저장" }));
    await waitFor(() => expect(productService.saveCells).toHaveBeenLastCalledWith(1, []));
  });

  it("retains edits across a failed save and background refetch", async () => {
    vi.mocked(productService.saveCells).mockRejectedValueOnce(new Error("Unavailable"));
    const { client } = setup();
    const a = await screen.findByRole("checkbox", { name: "Cell A (CELL-A)" });
    fireEvent.click(a);
    fireEvent.click(screen.getByRole("button", { name: "Cell 저장" }));
    await screen.findByRole("alert");
    await client.invalidateQueries({ queryKey: ["product-cells", 1] });
    expect(a).toBeChecked();
    fireEvent.click(screen.getByRole("button", { name: "Cell 저장" }));
    await screen.findByText("Cell 저장 완료");
    expect(productService.saveCells).toHaveBeenLastCalledWith(1, [1]);
  });

  it("does not allow an empty save after a load error", async () => {
    vi.mocked(productService.getCells).mockRejectedValue(new Error("Unavailable"));
    setup();
    await screen.findByRole("alert");
    expect(screen.getByRole("button", { name: "Cell 저장" })).toBeDisabled();
    expect(productService.saveCells).not.toHaveBeenCalled();
  });
});
