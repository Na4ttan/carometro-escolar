export interface Turma {
  id: number;
  nome: string;
  nivel_ensino: 'fundamental' | 'medio';
  serie: number;
  turno: string;
  sala?: string | null;
  ano: number;
  ativo: boolean;
}
