import { useState, useEffect } from "react";
import styles from "./WorthlessCounter.module.css";

interface WorthlessCounterProps {
    value?: number;
}

export function WorthlessCounter({ value }: WorthlessCounterProps) {
    const [displayValue, setDisplayValue] = useState<number | undefined>(value);
    const [isFading, setIsFading] = useState(false);

    useEffect(() => {
        if (value !== displayValue) {
            setIsFading(true);
            const timer = setTimeout(() => {
                setDisplayValue(value);
                setIsFading(false);
            }, 300);
            return () => clearTimeout(timer);
        }
    }, [value, displayValue]);

    return (
        <div className={styles.container}>
            <div className={styles.label}>Worthless Counter</div>
            <div className={`${styles.counter} ${isFading ? styles.fade : ""}`}>
                {displayValue ?? "—"}
            </div>
        </div>
    );
}