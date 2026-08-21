import { api } from "./api";
import { SecurityReport } from "@/types/report";

export async function getSecurityReport() {
    const response = await api.get<SecurityReport>(
        "/reports/security-summary"
    );

    return response.data;
}