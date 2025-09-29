import styles from "./WorthlessCounter.module.css";

interface WorthlessCounterProps {
    value?: number;
}

export function WorthlessCounter({ value }: WorthlessCounterProps) {
    return (
        <div className={styles.container}>
            <div className={styles.label}>Worthless Counter</div>
            <div className={styles.counter} key={value}>
                {value ?? "—"}
            </div>
        </div>
    );
}