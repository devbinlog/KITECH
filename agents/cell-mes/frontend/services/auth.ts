import api from "@/lib/axios";
import { Token, User } from "@/types";

export const authService = {
  async login(username: string, password: string): Promise<Token> {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const response = await api.post<Token>("/api/v1/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return response.data;
  },

  async register(username: string, password: string, role: string = "OPERATOR"): Promise<User> {
    const response = await api.post<User>("/api/v1/auth/register", {
      username,
      password,
      role,
    });
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>("/api/v1/auth/me");
    return response.data;
  },
};
