export interface UsuarioPerfil {
  tipo: 'escola' | 'professor';
  id: number;
  nome: string;
  email?: string;
  escola_nome?: string;
}