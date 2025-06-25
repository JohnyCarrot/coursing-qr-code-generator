import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { useRouter, useFocusEffect, Stack } from 'expo-router';
import { useCallback, useState } from 'react';
import { Alert, Button, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

export default function ScannerScreen() {
    const router = useRouter();
    const [facing, setFacing] = useState<CameraType>('back');
    const [permission, requestPermission] = useCameraPermissions();
    const [scanned, setScanned] = useState(false);

    // Reset čítačky pri návrate na túto obrazovku
    useFocusEffect(
        useCallback(() => {
            setScanned(false);
        }, [])
    );

    if (!permission) return <View />;
    if (!permission.granted) {
        return (
            <View style={styles.container}>
                <Text style={styles.message}>We need camera permission</Text>
                <Button title="Grant permission" onPress={requestPermission} />
            </View>
        );
    }

    function toggleCameraFacing() {
        setFacing(current => (current === 'back' ? 'front' : 'back'));
    }

    function handleBarCodeScanned({ data }: { data: string }) {
        setScanned(true);

        let parsed;
        try {
            parsed = JSON.parse(data);
        } catch {
            Alert.alert("Invalid QR Code", "QR code does not contain valid JSON.", [
                { text: "OK", onPress: () => setScanned(false) },
            ]);
            return;
        }

        if (!isValidDogData(parsed)) {
            Alert.alert("Invalid QR Data", "Required dog data is missing or incorrect.", [
                { text: "OK", onPress: () => setScanned(false) },
            ]);
            return;
        }

        router.push({
            pathname: "/dog-detail",
            params: { dogData: JSON.stringify(parsed.Dog) },
        });
    }

    return (
        <>
            <Stack.Screen options={{ headerShown: false, tabBarStyle: { display: 'none' } }} />
            <View style={styles.container}>
                <CameraView
                    style={styles.camera}
                    facing={facing}
                    barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
                    onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
                >
                    <View style={styles.buttonContainer}>
                        <TouchableOpacity style={styles.button} onPress={toggleCameraFacing}>
                            <Text style={styles.text}>Flip Camera</Text>
                        </TouchableOpacity>
                    </View>
                </CameraView>
            </View>
        </>
    );
}

function isValidDogData(data: any): boolean {
    if (!data || typeof data !== "object") return false;
    const dog = data.Dog;
    if (!dog) return false;

    const requiredFields = [
        "Name",
        "Breed",
        "Class",
        "Gender",
        "ChipNumber",
        "LicenseNumber",
        "PedigreeNumber",
        "BirthDate",
        "Owners",
    ];

    for (const field of requiredFields) {
        if (!(field in dog)) return false;
    }

    if (!Array.isArray(dog.Owners)) return false;

    for (const owner of dog.Owners) {
        const ownerFields = [
            "FirstName",
            "LastName",
            "StreetAndNumber",
            "PostalCodeAndCity",
            "Country",
        ];
        for (const f of ownerFields) {
            if (!(f in owner)) return false;
        }
    }

    return true;
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
    },
    message: {
        textAlign: 'center',
        paddingBottom: 10,
    },
    camera: {
        flex: 1,
    },
    buttonContainer: {
        flex: 1,
        flexDirection: 'row',
        backgroundColor: 'transparent',
        margin: 64,
    },
    button: {
        flex: 1,
        alignSelf: 'flex-end',
        alignItems: 'center',
    },
    text: {
        fontSize: 24,
        fontWeight: 'bold',
        color: 'white',
    },
});
