import { useLocalSearchParams, useRouter } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

export default function DogDetailScreen() {
    const params = useLocalSearchParams();
    const dog = JSON.parse(params.dogData as string);

    return (
        <ScrollView style={{ padding: 16 }}>
            <Text style={styles.heading}>Dog Information</Text>
            <View style={styles.card}>
                <Text><Text style={styles.label}>Name:</Text> {dog.Name}</Text>
                <Text><Text style={styles.label}>Breed:</Text> {dog.Breed}</Text>
                <Text><Text style={styles.label}>Class:</Text> {dog.Class}</Text>
                <Text><Text style={styles.label}>Gender:</Text> {dog.Gender}</Text>
                <Text><Text style={styles.label}>Chip Number:</Text> {dog.ChipNumber}</Text>
                <Text><Text style={styles.label}>License Number:</Text> {dog.LicenseNumber}</Text>
                <Text><Text style={styles.label}>Pedigree Number:</Text> {dog.PedigreeNumber}</Text>
                <Text><Text style={styles.label}>Birth Date:</Text> {dog.BirthDate}</Text>
            </View>

            <Text style={styles.heading}>Owners</Text>
            {dog.Owners.map((owner: any, index: number) => (
                <View key={index} style={styles.card}>
                    <Text style={styles.cardTitle}>Owner {index + 1}</Text>
                    <Text><Text style={styles.label}>Name:</Text> {owner.FirstName} {owner.LastName}</Text>
                    <Text><Text style={styles.label}>Street:</Text> {owner.StreetAndNumber}</Text>
                    <Text><Text style={styles.label}>City:</Text> {owner.PostalCodeAndCity}</Text>
                    <Text><Text style={styles.label}>Country:</Text> {owner.Country}</Text>
                </View>
            ))}
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    heading: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 12,
    },
    label: {
        fontWeight: 'bold',
    },
    card: {
        backgroundColor: '#f2f2f2',
        padding: 12,
        borderRadius: 10,
        marginBottom: 16,
    },
    cardTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 8,
    },
});
