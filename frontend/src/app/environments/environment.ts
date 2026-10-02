const porta = window.location.port;
const baseUrl = porta === '4200'
  ? `http://${window.location.hostname}:8000/api`
  : `${window.location.origin}/api`;

export const environment = {
  production: false,
  apiUrl: baseUrl
};