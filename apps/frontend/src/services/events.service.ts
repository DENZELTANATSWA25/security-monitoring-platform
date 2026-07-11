import {api} from "./api";
import {SecurityEvent} from "@/types/event";


export async function getEvents(){

    const response =
        await api.get<SecurityEvent[]>(
            "/events/"
        );


    return response.data;

}