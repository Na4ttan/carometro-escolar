export interface Aluno {
  id: number;
  nome_completo: string;
  nome_social: string | null;
  data_nascimento: string | null;
  matricula: string | null;
  foto: string | null;
  turma_id: number | null;
  turma_nome: string | null;
}