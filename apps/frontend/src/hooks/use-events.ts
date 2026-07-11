import {useQuery} from "@tanstack/react-query";
import {getEvents} from "@/services/events.service";

export function useEvents() {
    return useQuery({
        queryKey: ["security-events"],
        queryFn: getEvents
    });
}