import { adminAuth, customerAuth } from '../api/api';

export const authService = {
  login: (email, password) => customerAuth.login({ email, password }),
  register: (payload) => customerAuth.signup(payload),
  me: () => customerAuth.me(),
  logout: () => customerAuth.logout(),
  adminLogin: (usernameOrEmail, password) =>
    adminAuth.login({ username_or_email: usernameOrEmail, password }),
  adminMe: () => adminAuth.me(),
  adminLogout: () => adminAuth.logout()
};

export default authService;
