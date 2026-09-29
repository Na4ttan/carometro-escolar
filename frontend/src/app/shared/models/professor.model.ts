export interface Professor {
  id: number;
  nome_completo: string;
  email: string | null;
  matricula_funcional: string | null;
  foto: string | null;
  turmas_ids: number[];
  turmas_nomes: string[];
}