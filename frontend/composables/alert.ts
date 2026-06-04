import { reactive } from 'vue';

interface Alert {
    message: string;
    type: 'success' | 'info' | 'warning' | 'error' | 'neutral';
}
interface State {
    alerts: Alert[];
}

const state = reactive<State>({
    alerts: []
});

const addAlert = (message: string, type: Alert['type'] = 'error') => {
    // Do not display more than 3 alerts at a time
    if (state.alerts.length > 2) {
        state.alerts.shift();
    }

    // Add the new alert
    state.alerts.push({ message, type });

    // Automatically disappear after n milliseconds
    setTimeout(() => {
        state.alerts.shift();
    }, 3500);
};

export const useAlert = () => {
    return {
        state,
        addAlert
    };
};
